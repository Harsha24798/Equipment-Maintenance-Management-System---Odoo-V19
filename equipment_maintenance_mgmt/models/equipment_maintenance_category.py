from odoo import api, fields, models


class EquipmentMaintenanceCategory(models.Model):
    """Equipment category (Machinery, IT, Vehicles...): groups equipment for
    filtering and for the maintenance cost analysis."""
    # _name: technical name of the model -> PostgreSQL table "equipment_maintenance_category"
    _name = 'equipment.maintenance.category'
    # _description: human readable name shown in logs, access errors and technical menus
    _description = 'Equipment Category'
    # _order: default sort order of search() results and list views
    _order = 'name'

    # --- Fields -------------------------------------------------------------
    # translate=True: the name can be translated per language
    name = fields.Char(string='Category Name', required=True, translate=True)
    code = fields.Char(string='Code')
    # color: index of the Odoo colour palette (used by kanban / tags)
    color = fields.Integer(string='Color Index')
    description = fields.Text(string='Description')
    # active: False hides (archives) the record instead of deleting it
    active = fields.Boolean(string='Active', default=True)
    # Many2one -> res.company; default = the company currently selected by the user
    company_id = fields.Many2one(
        'res.company', string='Company', default=lambda self: self.env.company)
    # One2many: inverse side of equipment.category_id (no column in this table)
    equipment_ids = fields.One2many(
        'equipment.maintenance.equipment', 'category_id', string='Equipment')
    # Non-stored computed field: calculated on the fly by _compute_equipment_count
    equipment_count = fields.Integer(
        string='Equipment Count', compute='_compute_equipment_count')

    # --- SQL constraints ------------------------------------------------------
    # Odoo 19 syntax: models.Constraint(<SQL>, <error message>) replaces _sql_constraints.
    # PostgreSQL refuses two categories with the same name in the same company.
    _name_company_uniq = models.Constraint(
        'UNIQUE(name, company_id)',
        'A category with this name already exists in this company.',
    )

    # --- Compute methods ------------------------------------------------------
    # @api.depends: recompute when the listed fields change
    @api.depends('equipment_ids')
    def _compute_equipment_count(self):
        # _read_group returns [(category, count), ...] with ONE SQL query for all
        # categories (avoids one search_count() per record, the "N+1" problem)
        counts = dict(self.env['equipment.maintenance.equipment']._read_group(
            [('category_id', 'in', self.ids)], ['category_id'], ['__count'],
        ))
        for category in self:
            category.equipment_count = counts.get(category, 0)

    # --- Actions (called by buttons in the views) -----------------------------
    def action_view_equipment(self):
        """Smart button: open the equipment of this category."""
        # ensure_one(): this action works on a single record only
        self.ensure_one()
        # _for_xml_id: read an existing window action by its XML ID, then adapt it
        action = self.env['ir.actions.act_window']._for_xml_id(
            'equipment_maintenance_mgmt.equipment_maintenance_equipment_action')
        # domain: filter the records shown; context default_*: pre-fill new records
        action['domain'] = [('category_id', '=', self.id)]
        action['context'] = {'default_category_id': self.id}
        return action
