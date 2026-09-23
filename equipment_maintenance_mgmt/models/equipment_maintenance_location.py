from odoo import api, fields, models
from odoo.exceptions import ValidationError


class EquipmentMaintenanceLocation(models.Model):
    _name = 'equipment.maintenance.location'
    _description = 'Equipment Location'
    _parent_name = 'parent_id'
    _parent_store = True
    _rec_name = 'complete_name'
    _order = 'complete_name'

    name = fields.Char(string='Location Name', required=True, translate=True)
    complete_name = fields.Char(
        string='Full Location Name', compute='_compute_complete_name',
        recursive=True, store=True)
    parent_id = fields.Many2one(
        'equipment.maintenance.location', string='Parent Location',
        index=True, ondelete='cascade')
    parent_path = fields.Char(index=True)
    child_ids = fields.One2many(
        'equipment.maintenance.location', 'parent_id', string='Sub Locations')
    active = fields.Boolean(string='Active', default=True)
    company_id = fields.Many2one(
        'res.company', string='Company', default=lambda self: self.env.company)
    note = fields.Text(string='Address / Notes')

    @api.depends('name', 'parent_id.complete_name')
    def _compute_complete_name(self):
        for location in self:
            if location.parent_id:
                location.complete_name = f'{location.parent_id.complete_name} / {location.name}'
            else:
                location.complete_name = location.name

    @api.constrains('parent_id')
    def _check_parent_id(self):
        if self._has_cycle():
            raise ValidationError(self.env._('You cannot create recursive locations.'))
