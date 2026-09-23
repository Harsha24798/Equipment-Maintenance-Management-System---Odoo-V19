from odoo import api, fields, models
from odoo.exceptions import ValidationError


class EquipmentMaintenanceLocation(models.Model):
    """Hierarchical location of equipment, e.g. "Colombo Plant / Workshop A"."""
    _name = 'equipment.maintenance.location'
    _description = 'Equipment Location'
    # _parent_name: the Many2one field that points to the parent record
    _parent_name = 'parent_id'
    # _parent_store: maintain parent_path for fast 'child_of' / 'parent_of' searches
    _parent_store = True
    # _rec_name: field used as the display name (default would be 'name')
    _rec_name = 'complete_name'
    _order = 'complete_name'

    name = fields.Char(string='Location Name', required=True, translate=True)
    # Stored + recursive compute: depends on the parent's complete_name, which
    # itself depends on its parent... recursive=True tells the ORM about this chain
    complete_name = fields.Char(
        string='Full Location Name', compute='_compute_complete_name',
        recursive=True, store=True)
    # ondelete='cascade': deleting a parent deletes its sub-locations
    parent_id = fields.Many2one(
        'equipment.maintenance.location', string='Parent Location',
        index=True, ondelete='cascade')
    # parent_path: technical field required by _parent_store (e.g. "1/4/9/")
    parent_path = fields.Char(index=True)
    child_ids = fields.One2many(
        'equipment.maintenance.location', 'parent_id', string='Sub Locations')
    active = fields.Boolean(string='Active', default=True)
    company_id = fields.Many2one(
        'res.company', string='Company', default=lambda self: self.env.company)
    note = fields.Text(string='Address / Notes')

    # 'parent_id.complete_name': a dotted dependency -> recompute when the parent is renamed
    @api.depends('name', 'parent_id.complete_name')
    def _compute_complete_name(self):
        for location in self:
            if location.parent_id:
                location.complete_name = f'{location.parent_id.complete_name} / {location.name}'
            else:
                location.complete_name = location.name

    # @api.constrains: Python validation executed after create() / write() of parent_id
    @api.constrains('parent_id')
    def _check_parent_id(self):
        # _has_cycle(): ORM helper that detects A -> B -> A loops in the hierarchy
        if self._has_cycle():
            # ValidationError: blocking error shown to the user, the transaction is rolled back
            raise ValidationError(self.env._('You cannot create recursive locations.'))
