from random import randint

from odoo import fields, models


class EquipmentMaintenanceTag(models.Model):
    """Tag to classify maintenance requests (Electrical, Safety, Warranty Claim...)."""
    _name = 'equipment.maintenance.tag'
    _description = 'Maintenance Tag'
    _order = 'name'

    # --- Default methods ------------------------------------------------------
    def _default_color(self):
        # Random colour index of the Odoo palette for every new tag
        return randint(1, 11)

    # --- Fields -----------------------------------------------------------------
    name = fields.Char(string='Tag Name', required=True, translate=True)
    color = fields.Integer(string='Color', default=_default_color)
    active = fields.Boolean(string='Active', default=True)
    # Many2many: same relation table and columns as request.tag_ids, seen from the tag side
    request_ids = fields.Many2many(
        'equipment.maintenance.request', 'equipment_maintenance_request_tag_rel',
        'tag_id', 'request_id', string='Maintenance Requests')

    # --- SQL constraints --------------------------------------------------------
    _name_uniq = models.Constraint('UNIQUE(name)', 'A tag with this name already exists.')
