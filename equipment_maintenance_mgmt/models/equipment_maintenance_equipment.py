from datetime import timedelta

from odoo import api, fields, models
from odoo.exceptions import ValidationError
from odoo.fields import Domain

# Selection values: (technical value stored in DB, label shown to the user)
WARRANTY_STATES = [
    ('none', 'No Warranty'),
    ('valid', 'Under Warranty'),
    ('expiring', 'Expiring Soon'),
    ('expired', 'Expired'),
]


class EquipmentMaintenanceEquipment(models.Model):
    """Equipment master: every asset of the company that can be maintained."""
    _name = 'equipment.maintenance.equipment'
    _description = 'Maintenance Equipment'
    # _inherit (list of mixins) adds features without extra code:
    #   mail.thread         -> chatter: messages, followers, field tracking
    #   mail.activity.mixin -> activities (to-dos) on the record
    #   image.mixin         -> image_1920 ... image_128 fields (photo of the equipment)
    _inherit = ['mail.thread', 'mail.activity.mixin', 'image.mixin']
    _order = 'name, id'
    # _rec_names_search: fields searched when typing in a Many2one (find by serial number)
    _rec_names_search = ['name', 'serial_no']
    # _check_company_auto: verify that Many2one fields with check_company=True
    # point to records of the same company
    _check_company_auto = True

    # --- Fields (requirement: equipment master) ------------------------------
    # tracking=True: every change is logged in the chatter
    name = fields.Char(string='Equipment Name', required=True, tracking=True)
    # copy=False: not duplicated by copy(); index=True: DB index for fast search
    serial_no = fields.Char(
        string='Serial Number', required=True, copy=False, tracking=True, index=True)
    # ondelete='restrict': a category used by equipment cannot be deleted
    category_id = fields.Many2one(
        'equipment.maintenance.category', string='Category', required=True,
        tracking=True, ondelete='restrict', check_company=True, index=True)
    location_id = fields.Many2one(
        'equipment.maintenance.location', string='Location', tracking=True,
        ondelete='restrict', check_company=True, index=True)
    purchase_date = fields.Date(string='Purchase Date', tracking=True)
    warranty_expiry_date = fields.Date(string='Warranty Expiry Date', tracking=True)
    # Many2one to hr.employee (module 'hr'): the person responsible for the asset
    employee_id = fields.Many2one(
        'hr.employee', string='Responsible Employee', tracking=True,
        ondelete='restrict', check_company=True, index=True)
    company_id = fields.Many2one(
        'res.company', string='Company', required=True, index=True,
        default=lambda self: self.env.company)
    # related field: value read from company_id.currency_id (not stored)
    currency_id = fields.Many2one(related='company_id.currency_id', string='Currency')
    # Monetary: amount displayed with the currency given by currency_field
    purchase_cost = fields.Monetary(string='Purchase Cost', currency_field='currency_id')
    model = fields.Char(string='Model')
    manufacturer = fields.Char(string='Manufacturer')
    note = fields.Html(string='Notes')
    active = fields.Boolean(string='Active', default=True, tracking=True)
    color = fields.Integer(string='Color Index')
    # One2many: all maintenance requests of this equipment (inverse of request.equipment_id)
    request_ids = fields.One2many(
        'equipment.maintenance.request', 'equipment_id', string='Maintenance Requests')
    # Two fields filled by the same compute method
    request_count = fields.Integer(
        string='Request Count', compute='_compute_request_count')
    open_request_count = fields.Integer(
        string='Open Requests', compute='_compute_request_count')
    # store=True: computed value saved in the DB -> can be searched, grouped, summed
    last_maintenance_date = fields.Date(
        string='Last Maintenance', compute='_compute_total_maintenance_cost', store=True)
    total_maintenance_cost = fields.Monetary(
        string='Total Maintenance Cost', currency_field='currency_id',
        compute='_compute_total_maintenance_cost', store=True,
        help="Sum of the total cost of all completed maintenance requests.")
    # Non-stored compute (depends on today's date) + search method so that it
    # can still be used in filters: see _search_warranty_state
    warranty_state = fields.Selection(
        WARRANTY_STATES, string='Warranty Status',
        compute='_compute_warranty_state', search='_search_warranty_state')
    warranty_days_left = fields.Integer(
        string='Warranty Days Left', compute='_compute_warranty_state')

    # --- SQL constraints (Odoo 19: models.Constraint) --------------------------
    # Business rule: one physical asset = one serial number per company
    _serial_no_company_uniq = models.Constraint(
        'UNIQUE(serial_no, company_id)',
        'The serial number must be unique per company.',
    )

    # --- Compute / search methods ---------------------------------------------
    # _compute_display_name: standard hook that builds the text shown in Many2one fields
    @api.depends('name', 'serial_no')
    def _compute_display_name(self):
        for equipment in self:
            if equipment.serial_no:
                equipment.display_name = f'{equipment.name} [{equipment.serial_no}]'
            else:
                equipment.display_name = equipment.name

    @api.depends('request_ids.state')
    def _compute_request_count(self):
        request_model = self.env['equipment.maintenance.request']
        # _read_group(domain, groupby, aggregates): one grouped SQL query for all records
        totals = dict(request_model._read_group(
            [('equipment_id', 'in', self.ids)], ['equipment_id'], ['__count']))
        opened = dict(request_model._read_group(
            [('equipment_id', 'in', self.ids),
             ('state', 'in', request_model._get_open_states())],
            ['equipment_id'], ['__count']))
        for equipment in self:
            equipment.request_count = totals.get(equipment, 0)
            equipment.open_request_count = opened.get(equipment, 0)

    # Dotted dependencies: recompute when a request's state / cost / done date changes
    @api.depends('request_ids.state', 'request_ids.total_cost', 'request_ids.date_done')
    def _compute_total_maintenance_cost(self):
        # Only completed work counts as actual maintenance cost of the asset;
        # running and cancelled requests are analysed in the cost report.
        for equipment in self:
            # filtered(): keep the records matching the condition (in memory)
            done = equipment.request_ids.filtered(lambda r: r.state == 'completed')
            # mapped(): list of the field values of all records
            equipment.total_maintenance_cost = sum(done.mapped('total_cost'))
            done_dates = [date_done for date_done in done.mapped('date_done') if date_done]
            equipment.last_maintenance_date = max(done_dates).date() if done_dates else False

    @api.depends('warranty_expiry_date', 'company_id.maintenance_warranty_alert_days')
    def _compute_warranty_state(self):
        # context_today: today's date in the user's timezone
        today = fields.Date.context_today(self)
        for equipment in self:
            expiry_date = equipment.warranty_expiry_date
            if not expiry_date:
                equipment.warranty_state = 'none'
                equipment.warranty_days_left = 0
                continue
            days_left = (expiry_date - today).days
            equipment.warranty_days_left = max(days_left, 0)
            if days_left < 0:
                equipment.warranty_state = 'expired'
            elif days_left <= equipment.company_id.maintenance_warranty_alert_days:
                equipment.warranty_state = 'expiring'
            else:
                equipment.warranty_state = 'valid'

    def _search_warranty_state(self, operator, value):
        """Translate warranty states into date domains so that the
        non-stored field can be used in search filters."""
        # Odoo 19 normalises '=' / '!=' into 'in' / 'not in'; returning
        # NotImplemented for 'not in' lets the ORM negate the 'in' domain.
        if operator != 'in':
            return NotImplemented
        today = fields.Date.context_today(self)
        alert_date = today + timedelta(days=self.env.company.maintenance_warranty_alert_days)
        # A domain is a list of (field, operator, value) conditions
        state_domains = {
            'none': [('warranty_expiry_date', '=', False)],
            'expired': [('warranty_expiry_date', '<', today)],
            'expiring': [('warranty_expiry_date', '>=', today),
                         ('warranty_expiry_date', '<=', alert_date)],
            'valid': [('warranty_expiry_date', '>', alert_date)],
        }
        # Domain.OR: combine the domains of the requested states with OR
        return Domain.OR(state_domains[state] for state in value if state in state_domains)

    # --- Constraints -----------------------------------------------------------
    @api.constrains('purchase_date', 'warranty_expiry_date')
    def _check_dates(self):
        today = fields.Date.context_today(self)
        for equipment in self:
            if equipment.purchase_date and equipment.purchase_date > today:
                # self.env._(): translatable message with named placeholders
                raise ValidationError(self.env._(
                    "The purchase date of '%(name)s' cannot be in the future.",
                    name=equipment.name))
            if (equipment.purchase_date and equipment.warranty_expiry_date
                    and equipment.warranty_expiry_date < equipment.purchase_date):
                raise ValidationError(self.env._(
                    "The warranty expiry date of '%(name)s' must be on or after "
                    "its purchase date.", name=equipment.name))

    # --- ORM overrides ---------------------------------------------------------
    def copy_data(self, default=None):
        # copy_data() prepares the values used by copy() (Duplicate action);
        # super() calls the standard implementation first
        vals_list = super().copy_data(default=default)
        for equipment, vals in zip(self, vals_list, strict=True):
            vals.setdefault('name', self.env._('%s (copy)', equipment.name))
        return vals_list

    # --- Actions (buttons) -----------------------------------------------------
    def action_view_requests(self):
        """Smart button: open the maintenance requests of this equipment."""
        self.ensure_one()
        action = self.env['ir.actions.act_window']._for_xml_id(
            'equipment_maintenance_mgmt.equipment_maintenance_request_action')
        action['domain'] = [('equipment_id', '=', self.id)]
        action['context'] = {'default_equipment_id': self.id}
        return action

    def action_create_request(self):
        """Header button "New Request": open an empty request form for this equipment."""
        self.ensure_one()
        # A method can return an action dictionary that the web client executes
        return {
            'type': 'ir.actions.act_window',
            'name': self.env._('New Maintenance Request'),
            'res_model': 'equipment.maintenance.request',
            'view_mode': 'form',
            'target': 'current',
            'context': {'default_equipment_id': self.id},
        }

    def action_print_history(self):
        """Header button "Print History": render the QWeb PDF report."""
        # env.ref(): get a record by its XML ID; report_action() prints it for self
        return self.env.ref(
            'equipment_maintenance_mgmt.equipment_maintenance_equipment_action_report_history',
        ).report_action(self)

    # --- Scheduled action (cron) -----------------------------------------------
    # @api.model: the method does not depend on specific records (called on the model)
    @api.model
    def _cron_warranty_expiry_reminder(self):
        """Schedule a reminder activity for the responsible employee's user
        when the warranty of an equipment is about to expire. Runs daily."""
        xmlid = 'equipment_maintenance_mgmt.mail_activity_data_warranty_expiry'
        activity_type = self.env.ref(xmlid, raise_if_not_found=False)
        if not activity_type:
            return
        # search(domain): return the records matching the domain
        equipments = self.search([
            ('warranty_state', '=', 'expiring'),
            ('employee_id.user_id', '!=', False),
        ])
        for equipment in equipments:
            responsible_user = equipment.employee_id.user_id
            # Only remind users who can open the equipment (maintenance groups)
            if not responsible_user.has_group(
                    'equipment_maintenance_mgmt.equipment_maintenance_mgmt_group_technician'):
                continue
            # Idempotent: do not create the reminder twice
            if equipment.activity_ids.filtered(lambda a: a.activity_type_id == activity_type):
                continue
            # activity_schedule(): helper of mail.activity.mixin that creates a to-do
            equipment.activity_schedule(
                xmlid,
                date_deadline=equipment.warranty_expiry_date,
                user_id=responsible_user.id,
                summary=self.env._('Warranty expires on %s', equipment.warranty_expiry_date),
            )
