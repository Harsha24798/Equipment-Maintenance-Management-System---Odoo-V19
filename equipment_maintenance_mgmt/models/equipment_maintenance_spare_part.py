from odoo import api, fields, models


class EquipmentMaintenanceSparePart(models.Model):
    _name = 'equipment.maintenance.spare.part'
    _description = 'Maintenance Spare Part Consumption'
    _inherit = ['equipment.maintenance.line.mixin']
    _order = 'id'

    product_id = fields.Many2one(
        'product.product', string='Product', required=True, index=True,
        ondelete='restrict', domain=[('type', '=', 'consu')])
    name = fields.Char(
        string='Description', compute='_compute_name', store=True,
        readonly=False, precompute=True)
    quantity = fields.Float(
        string='Quantity', required=True, default=1.0, digits='Product Unit')
    uom_id = fields.Many2one(related='product_id.uom_id', string='Unit')
    unit_cost = fields.Monetary(
        string='Unit Cost', currency_field='currency_id',
        compute='_compute_unit_cost', store=True, readonly=False, precompute=True,
        help="Defaults to the cost of the product; can be adjusted per consumption.")
    total_cost = fields.Monetary(
        string='Total Cost', currency_field='currency_id',
        compute='_compute_total_cost', store=True, aggregator='sum')

    _quantity_positive = models.Constraint(
        'CHECK(quantity > 0)', 'The spare part quantity must be greater than zero.')
    _unit_cost_positive = models.Constraint(
        'CHECK(unit_cost >= 0)', 'The spare part unit cost cannot be negative.')

    @api.depends('product_id')
    def _compute_name(self):
        for line in self:
            line.name = line.product_id.display_name or False

    @api.depends('product_id', 'request_id.company_id')
    def _compute_unit_cost(self):
        for line in self:
            company = line.request_id.company_id or self.env.company
            line.unit_cost = line.product_id.with_company(company).standard_price

    @api.depends('quantity', 'unit_cost')
    def _compute_total_cost(self):
        # Spare part cost of one line = quantity x unit cost
        for line in self:
            line.total_cost = line.quantity * line.unit_cost
