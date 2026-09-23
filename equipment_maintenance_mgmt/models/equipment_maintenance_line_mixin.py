from odoo import api, fields, models
from odoo.exceptions import UserError

# Requests in these states can no longer receive activity / spare part changes
LOCKED_REQUEST_STATES = ('completed', 'cancelled')


class EquipmentMaintenanceLineMixin(models.AbstractModel):
    """Common behaviour of maintenance request lines (activities and spare
    parts): link to the request, company/currency propagation and locking of
    the lines once the request is completed or cancelled."""
    # AbstractModel: no database table; its fields and methods are copied into
    # every model that inherits it (_inherit = ['equipment.maintenance.line.mixin'])
    _name = 'equipment.maintenance.line.mixin'
    _description = 'Maintenance Request Line Mixin'

    # ondelete='cascade': deleting the request deletes its lines
    request_id = fields.Many2one(
        'equipment.maintenance.request', string='Maintenance Request',
        required=True, index=True, ondelete='cascade')
    request_state = fields.Selection(related='request_id.state', string='Request Status')
    # Stored related fields: allow grouping lines by equipment and multi-company rules
    equipment_id = fields.Many2one(
        related='request_id.equipment_id', store=True, string='Equipment')
    company_id = fields.Many2one(
        related='request_id.company_id', store=True, string='Company', index=True)
    currency_id = fields.Many2one(related='request_id.currency_id', string='Currency')

    # --- CRUD: every way of changing a line checks that the request is still open ---
    @api.model_create_multi
    def create(self, vals_list):
        request_ids = {vals['request_id'] for vals in vals_list if vals.get('request_id')}
        # browse(ids): get the records of these ids without querying the database yet
        self._check_request_editable(
            self.env['equipment.maintenance.request'].browse(request_ids))
        return super().create(vals_list)

    def write(self, vals):
        self._check_request_editable(self.request_id)
        # Also refuse moving a line to another (closed) request
        if vals.get('request_id'):
            self._check_request_editable(
                self.env['equipment.maintenance.request'].browse(vals['request_id']))
        return super().write(vals)

    @api.ondelete(at_uninstall=False)
    def _unlink_except_locked_request(self):
        self._check_request_editable(self.request_id)

    def _check_request_editable(self, requests):
        """Raise a UserError if one of ``requests`` is completed or cancelled."""
        locked_requests = requests.filtered(lambda r: r.state in LOCKED_REQUEST_STATES)
        if locked_requests:
            raise UserError(self.env._(
                "Lines of completed or cancelled maintenance requests cannot be "
                "modified (%(names)s).", names=', '.join(locked_requests.mapped('name'))))
