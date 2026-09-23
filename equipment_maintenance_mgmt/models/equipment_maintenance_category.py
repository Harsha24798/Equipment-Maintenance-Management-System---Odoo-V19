from odoo import api, fields, models


class EquipmentMaintenanceCategory(models.Model):
    _name = 'equipment.maintenance.category'
    _description = 'Equipment Category'
    _order = 'name'

    name = fields.Char(string='Category Name', required=True, translate=True)
    code = fields.Char(string='Code')
    color = fields.Integer(string='Color Index')
    description = fields.Text(string='Description')
    active = fields.Boolean(string='Active', default=True)
    company_id = fields.Many2one(
        'res.company', string='Company', default=lambda self: self.env.company)
    equipment_ids = fields.One2many(
        'equipment.maintenance.equipment', 'category_id', string='Equipment')
    equipment_count = fields.Integer(
        string='Equipment Count', compute='_compute_equipment_count')

    _name_company_uniq = models.Constraint(
        'UNIQUE(name, company_id)',
        'A category with this name already exists in this company.',
    )

    @api.depends('equipment_ids')
    def _compute_equipment_count(self):
        counts = dict(self.env['equipment.maintenance.equipment']._read_group(
            [('category_id', 'in', self.ids)], ['category_id'], ['__count'],
        ))
        for category in self:
            category.equipment_count = counts.get(category, 0)

    def action_view_equipment(self):
        self.ensure_one()
        action = self.env['ir.actions.act_window']._for_xml_id(
            'equipment_maintenance_mgmt.equipment_maintenance_equipment_action')
        action['domain'] = [('category_id', '=', self.id)]
        action['context'] = {'default_category_id': self.id}
        return action
