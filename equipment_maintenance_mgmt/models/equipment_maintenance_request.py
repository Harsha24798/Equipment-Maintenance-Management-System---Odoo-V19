from odoo import api, fields, models
from odoo.exceptions import UserError, ValidationError

REQUEST_STATES = [
    ('new', 'New'),
    ('assigned', 'Assigned'),
    ('in_progress', 'In Progress'),
    ('completed', 'Completed'),
    ('cancelled', 'Cancelled'),
]

REQUEST_TYPES = [
    ('corrective', 'Corrective'),
    ('preventive', 'Preventive'),
    ('inspection', 'Inspection'),
    ('calibration', 'Calibration'),
]

PRIORITIES = [
    ('0', 'Low'),
    ('1', 'Normal'),
    ('2', 'High'),
    ('3', 'Urgent'),
]

# Workflow definition: target state -> states it can be reached from.
#   new -> assigned -> in_progress -> completed
#   new / assigned / in_progress -> cancelled -> new (reset)
ALLOWED_TRANSITIONS = {
    'assigned': ('new',),
    'in_progress': ('assigned',),
    'completed': ('in_progress',),
    'cancelled': ('new', 'assigned', 'in_progress'),
    'new': ('cancelled',),
}

TODO_ACTIVITY_XMLID = 'equipment_maintenance_mgmt.mail_activity_data_maintenance_todo'


class EquipmentMaintenanceRequest(models.Model):
    _name = 'equipment.maintenance.request'
    _description = 'Maintenance Request'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'priority desc, request_date desc, id desc'
    _check_company_auto = True

    def _default_technician_domain(self):
        """Only internal users of the Technician group (or Manager, which
        implies it) can be assigned to a request."""
        group = self.env.ref(
            'equipment_maintenance_mgmt.equipment_maintenance_mgmt_group_technician',
            raise_if_not_found=False)
        domain = [('share', '=', False)]
        if group:
            domain.append(('all_group_ids', 'in', group.ids))
        return domain

    name = fields.Char(
        string='Request Number', required=True, readonly=True, copy=False,
        index='trigram', default=lambda self: self.env._('New'))
    equipment_id = fields.Many2one(
        'equipment.maintenance.equipment', string='Equipment', required=True,
        tracking=True, ondelete='restrict', check_company=True, index=True)
    request_date = fields.Date(
        string='Request Date', required=True, tracking=True,
        default=fields.Date.context_today)
    scheduled_date = fields.Date(string='Scheduled Date', tracking=True)
    request_type = fields.Selection(
        REQUEST_TYPES, string='Request Type', required=True,
        default='corrective', tracking=True)
    description = fields.Html(string='Description')
    technician_id = fields.Many2one(
        'res.users', string='Assigned Technician', tracking=True, index=True,
        domain=lambda self: self._default_technician_domain())
    tag_ids = fields.Many2many(
        'equipment.maintenance.tag', 'equipment_maintenance_request_tag_rel',
        'request_id', 'tag_id', string='Tags')
    priority = fields.Selection(
        PRIORITIES, string='Priority', default='1', required=True, tracking=True)
    state = fields.Selection(
        REQUEST_STATES, string='Status', required=True, default='new',
        readonly=True, copy=False, tracking=True, index=True, group_expand=True)
    company_id = fields.Many2one(
        'res.company', string='Company', required=True, index=True,
        default=lambda self: self.env.company)
    currency_id = fields.Many2one(related='company_id.currency_id', string='Currency')
    # Master data of the equipment, stored to group and filter in reports
    category_id = fields.Many2one(
        related='equipment_id.category_id', store=True, string='Category')
    location_id = fields.Many2one(
        related='equipment_id.location_id', store=True, string='Location')
    employee_id = fields.Many2one(
        related='equipment_id.employee_id', string='Responsible Employee')
    date_start = fields.Datetime(string='Started On', readonly=True, copy=False)
    date_done = fields.Datetime(string='Completed On', readonly=True, copy=False)
    duration = fields.Float(
        string='Duration (Hours)', compute='_compute_duration', store=True,
        help="Elapsed time between the start and the completion of the request.")
    cancel_reason = fields.Text(string='Cancellation Reason', copy=False, tracking=True)
    resolution_note = fields.Html(string='Resolution Notes', copy=False)
    is_overdue = fields.Boolean(
        string='Overdue', compute='_compute_is_overdue', search='_search_is_overdue')
    # NOTE: named work_activity_ids to avoid a clash with activity_ids of mail.activity.mixin
    work_activity_ids = fields.One2many(
        'equipment.maintenance.activity', 'request_id', string='Maintenance Activities',
        copy=False)
    spare_part_ids = fields.One2many(
        'equipment.maintenance.spare.part', 'request_id', string='Spare Parts',
        copy=False)
    total_hours = fields.Float(
        string='Total Hours', compute='_compute_costs', store=True)
    labour_cost = fields.Monetary(
        string='Labour Cost', currency_field='currency_id',
        compute='_compute_costs', store=True, aggregator='sum')
    spare_part_cost = fields.Monetary(
        string='Spare Part Cost', currency_field='currency_id',
        compute='_compute_costs', store=True, aggregator='sum')
    total_cost = fields.Monetary(
        string='Total Maintenance Cost', currency_field='currency_id',
        compute='_compute_costs', store=True, aggregator='sum', tracking=True)

    @api.depends('date_start', 'date_done')
    def _compute_duration(self):
        for request in self:
            if request.date_start and request.date_done:
                delta = request.date_done - request.date_start
                request.duration = delta.total_seconds() / 3600.0
            else:
                request.duration = 0.0

    @api.depends('scheduled_date', 'state')
    def _compute_is_overdue(self):
        today = fields.Date.context_today(self)
        open_states = self._get_open_states()
        for request in self:
            request.is_overdue = bool(
                request.scheduled_date
                and request.scheduled_date < today
                and request.state in open_states)

    def _search_is_overdue(self, operator, value):
        if operator != 'in':
            return NotImplemented
        today = fields.Date.context_today(self)
        overdue_domain = [
            ('scheduled_date', '<', today),
            ('state', 'in', self._get_open_states()),
        ]
        return overdue_domain if True in value else ['!', '&', *overdue_domain]

    @api.depends('work_activity_ids.hours_spent', 'work_activity_ids.cost',
                 'spare_part_ids.total_cost')
    def _compute_costs(self):
        # Total maintenance cost = labour cost (sum of hours x rate of every activity)
        #                        + spare part cost (sum of quantity x unit cost)
        for request in self:
            request.total_hours = sum(request.work_activity_ids.mapped('hours_spent'))
            request.labour_cost = sum(request.work_activity_ids.mapped('cost'))
            request.spare_part_cost = sum(request.spare_part_ids.mapped('total_cost'))
            request.total_cost = request.labour_cost + request.spare_part_cost

    @api.constrains('request_date', 'scheduled_date')
    def _check_scheduled_date(self):
        for request in self:
            if (request.scheduled_date and request.request_date
                    and request.scheduled_date < request.request_date):
                raise ValidationError(self.env._(
                    "The scheduled date of %(name)s cannot be before its request date.",
                    name=request.name))

    @api.constrains('equipment_id')
    def _check_equipment_id(self):
        for request in self:
            if not request.equipment_id.active:
                raise ValidationError(self.env._(
                    "You cannot create a maintenance request for the archived "
                    "equipment '%(equipment)s'.",
                    equipment=request.equipment_id.display_name))

    @api.constrains('technician_id', 'state')
    def _check_technician_id(self):
        # Data consistency: a request that is assigned, running or done must
        # always keep a responsible technician (e.g. it cannot be cleared).
        for request in self:
            if request.state in ('assigned', 'in_progress', 'completed') and not request.technician_id:
                raise ValidationError(self.env._(
                    "Request %(name)s must have an assigned technician in state '%(state)s'.",
                    name=request.name, state=dict(REQUEST_STATES)[request.state]))

    @api.onchange('equipment_id')
    def _onchange_equipment_id(self):
        """Warn the user (without blocking) when the selected equipment already
        has open requests, to avoid duplicate requests, or when it is still
        under warranty, so a supplier warranty claim can be considered."""
        if not self.equipment_id:
            return None
        open_requests = self.search([
            ('equipment_id', '=', self.equipment_id.id),
            ('state', 'in', self._get_open_states()),
            ('id', '!=', self._origin.id),
        ])
        messages = []
        if open_requests:
            messages.append(self.env._(
                "This equipment already has open maintenance request(s): %(names)s.",
                names=', '.join(open_requests.mapped('name'))))
        if self.equipment_id.warranty_state in ('valid', 'expiring'):
            messages.append(self.env._(
                "This equipment is under warranty until %(date)s: consider a "
                "warranty claim with the supplier.",
                date=self.equipment_id.warranty_expiry_date))
        if messages:
            return {'warning': {
                'title': self.env._('Please check'),
                'message': '\n\n'.join(messages),
            }}
        return None

    @api.model_create_multi
    def create(self, vals_list):
        default_name = self.env._('New')
        for vals in vals_list:
            if vals.get('name', default_name) == default_name:
                company_id = vals.get('company_id') or self.env.company.id
                vals['name'] = self.env['ir.sequence'].with_company(company_id).next_by_code(
                    'equipment.maintenance.request') or default_name
            # A request created with a technician is directly assigned
            if vals.get('technician_id') and vals.get('state', 'new') == 'new':
                vals['state'] = 'assigned'
        requests = super().create(vals_list)
        requests.filtered(lambda r: r.state == 'assigned')._schedule_technician_todo()
        return requests

    def write(self, vals):
        # Setting a technician on a new request moves it to "Assigned"
        requests_to_assign = self.env['equipment.maintenance.request']
        if vals.get('technician_id') and 'state' not in vals:
            requests_to_assign = self.filtered(lambda r: r.state == 'new')
        technician_changed = self.env['equipment.maintenance.request']
        if 'technician_id' in vals:
            technician_changed = self.filtered(
                lambda r: r.technician_id.id != vals['technician_id'])
        res = super().write(vals)
        if requests_to_assign:
            requests_to_assign.write({'state': 'assigned'})
        technician_changed.filtered(
            lambda r: r.state in ('assigned', 'in_progress'))._schedule_technician_todo()
        return res

    @api.ondelete(at_uninstall=False)
    def _unlink_except_processed(self):
        for request in self:
            if request.state not in ('new', 'cancelled'):
                raise UserError(self.env._(
                    "Only new or cancelled maintenance requests can be deleted "
                    "(%(name)s is '%(state)s'). Cancel it first.",
                    name=request.name, state=dict(REQUEST_STATES)[request.state]))

    def action_assign(self):
        self._check_state_transition('assigned')
        for request in self:
            if not request.technician_id:
                raise UserError(self.env._(
                    "Please select a technician before assigning request %(name)s.",
                    name=request.name))
        self.write({'state': 'assigned'})
        self._schedule_technician_todo()
        return True

    def action_start(self):
        self._check_state_transition('in_progress')
        self._check_is_assigned_technician()
        self.write({'state': 'in_progress', 'date_start': fields.Datetime.now()})
        return True

    def action_complete(self):
        self._check_state_transition('completed')
        self._check_is_assigned_technician()
        for request in self:
            if not request.work_activity_ids:
                raise UserError(self.env._(
                    "Record at least one maintenance activity before completing "
                    "request %(name)s.", name=request.name))
        self.write({'state': 'completed', 'date_done': fields.Datetime.now()})
        # Mark the technician's to-do as done
        self.activity_feedback([TODO_ACTIVITY_XMLID], feedback=self.env._('Maintenance completed.'))
        return True

    def action_cancel(self):
        self._check_state_transition('cancelled')
        self.write({'state': 'cancelled'})
        self.activity_unlink([TODO_ACTIVITY_XMLID])
        return True

    def action_reset_to_new(self):
        self._check_state_transition('new')
        self.write({
            'state': 'new',
            'technician_id': False,
            'date_start': False,
            'date_done': False,
            'cancel_reason': False,
        })
        return True

    def action_print_request(self):
        return self.env.ref(
            'equipment_maintenance_mgmt.equipment_maintenance_request_action_report',
        ).report_action(self)

    @api.model
    def _get_open_states(self):
        """States in which a request is still pending (used by reports,
        filters and the overdue computation)."""
        return ['new', 'assigned', 'in_progress']

    def _check_state_transition(self, target_state):
        """Raise a UserError if one of the requests cannot move to ``target_state``."""
        state_labels = dict(REQUEST_STATES)
        allowed_states = ALLOWED_TRANSITIONS[target_state]
        for request in self:
            if request.state not in allowed_states:
                raise UserError(self.env._(
                    "Request %(name)s cannot be set to '%(target)s' from state '%(state)s'.",
                    name=request.name, target=state_labels[target_state],
                    state=state_labels[request.state]))

    def _check_is_assigned_technician(self):
        """Only the assigned technician may start / complete the job: a user
        cannot perform (and close) work assigned to someone else, e.g. a
        request they reported themselves. Managers may act on any request."""
        if self.env.user.has_group('equipment_maintenance_mgmt.equipment_maintenance_mgmt_group_manager'):
            return
        for request in self:
            if request.technician_id != self.env.user:
                raise UserError(self.env._(
                    "Only the assigned technician (%(technician)s) or a maintenance "
                    "manager can process request %(name)s.",
                    technician=request.technician_id.name, name=request.name))

    def _schedule_technician_todo(self):
        """Plan a 'Maintenance To-Do' activity for the assigned technician,
        replacing any previous one (e.g. after a technician change)."""
        if not self.env.ref(TODO_ACTIVITY_XMLID, raise_if_not_found=False):
            return
        for request in self.filtered('technician_id'):
            request.activity_unlink([TODO_ACTIVITY_XMLID])
            request.activity_schedule(
                TODO_ACTIVITY_XMLID,
                user_id=request.technician_id.id,
                date_deadline=request.scheduled_date or fields.Date.context_today(request),
                summary=self.env._('Maintenance of %s', request.equipment_id.display_name),
            )

    @api.model
    def _cron_overdue_requests(self):
        """Post a reminder on overdue requests, notifying the technician. Runs daily."""
        overdue_requests = self.search([
            ('is_overdue', '=', True),
            ('technician_id', '!=', False),
        ])
        for request in overdue_requests:
            request.message_post(
                body=self.env._(
                    'This maintenance request is overdue (scheduled on %s).',
                    request.scheduled_date),
                partner_ids=request.technician_id.partner_id.ids,
                message_type='comment',
                subtype_xmlid='mail.mt_note',
            )
