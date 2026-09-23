from random import randint

from odoo import fields, models


class EquipmentMaintenanceTag(models.Model):
    _name = 'equipment.maintenance.tag'
    _description = 'Maintenance Tag'
    _order = 'name'

    def _default_color(self):
        return randint(1, 11)

    name = fields.Char(string='Tag Name', required=True, translate=True)
    color = fields.Integer(string='Color', default=_default_color)
    active = fields.Boolean(string='Active', default=True)
    request_ids = fields.Many2many(
        'equipment.maintenance.request', 'equipment_maintenance_request_tag_rel',
        'tag_id', 'request_id', string='Maintenance Requests')

    _name_uniq = models.Constraint('UNIQUE(name)', 'A tag with this name already exists.')
