from odoo import api, fields, models


class EquipmentMaintenanceSparePart(models.Model):
    """Spare part consumed on a request (requirement: spare parts consumption):
    product, quantity, unit cost and total cost."""
    _name = 'equipment.maintenance.spare.part'
    _description = 'Maintenance Spare Part Consumption'
    # Same shared behaviour as activities (request link, company, locking)
    _inherit = ['equipment.maintenance.line.mixin']
    _order = 'id'

    # --- Fields -------------------------------------------------------------------
    # domain: only goods ('consu') can be selected, not services
    product_id = fields.Many2one(
        'product.product', string='Product', required=True, index=True,
        ondelete='restrict', domain=[('type', '=', 'consu')])
    # Editable compute: proposed from the product name, can be changed
    name = fields.Char(
        string='Description', compute='_compute_name', store=True,
        readonly=False, precompute=True)
    # digits='Product Unit': decimal precision configured in Odoo (Odoo 19 name)
    quantity = fields.Float(
        string='Quantity', required=True, default=1.0, digits='Product Unit')
    uom_id = fields.Many2one(related='product_id.uom_id', string='Unit')
    # Editable compute: proposed from the product cost, can be adjusted per line
    unit_cost = fields.Monetary(
        string='Unit Cost', currency_field='currency_id',
        compute='_compute_unit_cost', store=True, readonly=False, precompute=True,
        help="Defaults to the cost of the product; can be adjusted per consumption.")
    total_cost = fields.Monetary(
        string='Total Cost', currency_field='currency_id',
        compute='_compute_total_cost', store=True, aggregator='sum')

    # --- SQL constraints ----------------------------------------------------------
    _quantity_positive = models.Constraint(
        'CHECK(quantity > 0)', 'The spare part quantity must be greater than zero.')
    _unit_cost_positive = models.Constraint(
        'CHECK(unit_cost >= 0)', 'The spare part unit cost cannot be negative.')

    # --- Compute methods ----------------------------------------------------------
    @api.depends('product_id')
    def _compute_name(self):
        for line in self:
            line.name = line.product_id.display_name or False

    @api.depends('product_id', 'request_id.company_id')
    def _compute_unit_cost(self):
        for line in self:
            company = line.request_id.company_id or self.env.company
            # standard_price (product cost) is company dependent -> with_company()
            line.unit_cost = line.product_id.with_company(company).standard_price

    @api.depends('quantity', 'unit_cost')
    def _compute_total_cost(self):
        # Spare part cost of one line = quantity x unit cost
        for line in self:
            line.total_cost = line.quantity * line.unit_cost
