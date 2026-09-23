from odoo import api, fields, models
from odoo.exceptions import ValidationError


class EquipmentMaintenanceActivity(models.Model):
    """Technician activity on a request (requirement: maintenance activities):
    what was done, by whom, how long, at which hourly rate and the cost."""
    _name = 'equipment.maintenance.activity'
    _description = 'Maintenance Activity'
    # Inherit the abstract line mixin: request_id, equipment_id, company_id,
    # currency_id and the "locked when request is closed" rules
    _inherit = ['equipment.maintenance.line.mixin']
    _order = 'date desc, id'

    # --- Default methods ------------------------------------------------------
    def _default_technician_id(self):
        """Default to the technician of the request, else the current user."""
        # context key default_request_id is set by the request form (context="{'default_request_id': id}")
        request_id = self.env.context.get('default_request_id')
        if request_id:
            request = self.env['equipment.maintenance.request'].browse(request_id)
            if request.technician_id:
                return request.technician_id
        return self.env.user

    # --- Fields (requirement: activity description, technician, hours, rate, cost) ---
    name = fields.Char(string='Activity Description', required=True)
    # default=<method>: value proposed when a new line is created
    technician_id = fields.Many2one(
        'res.users', string='Technician', required=True, index=True,
        default=_default_technician_id)
    date = fields.Date(string='Date', required=True, default=fields.Date.context_today)
    hours_spent = fields.Float(string='Hours Spent', required=True, default=1.0)
    # compute + store=True + readonly=False: a default computed from the technician
    # that the user can still overwrite; precompute=True computes it before INSERT
    labour_rate = fields.Monetary(
        string='Labour Rate', currency_field='currency_id',
        compute='_compute_labour_rate', store=True, readonly=False, precompute=True,
        help="Hourly rate. Defaults to the hourly cost of the technician's employee, "
             "otherwise to the default labour rate of the company.")
    cost = fields.Monetary(
        string='Cost', currency_field='currency_id',
        compute='_compute_cost', store=True, aggregator='sum')

    # --- SQL constraints (checked by PostgreSQL) ----------------------------------
    _hours_spent_positive = models.Constraint(
        'CHECK(hours_spent > 0)', 'Hours spent must be greater than zero.')
    _labour_rate_positive = models.Constraint(
        'CHECK(labour_rate >= 0)', 'The labour rate cannot be negative.')

    # --- Compute methods ----------------------------------------------------------
    @api.depends('technician_id', 'request_id.company_id')
    def _compute_labour_rate(self):
        for activity in self:
            company = activity.request_id.company_id or self.env.company
            # hourly_cost is restricted to HR officers (groups="hr.group_hr_user"):
            # read it with sudo, only the resulting rate is exposed on the line.
            # with_company(): read the company-specific employee of the user
            employee = activity.technician_id.sudo().with_company(company).employee_id
            activity.labour_rate = employee.hourly_cost or company.maintenance_labour_rate

    @api.depends('hours_spent', 'labour_rate')
    def _compute_cost(self):
        # Labour cost of one activity line = hours spent x hourly labour rate
        for activity in self:
            activity.cost = activity.hours_spent * activity.labour_rate

    # --- Python constraints ---------------------------------------------------------
    @api.constrains('hours_spent')
    def _check_hours_spent(self):
        for activity in self:
            if activity.hours_spent > 24:
                raise ValidationError(self.env._(
                    "An activity line cannot exceed 24 hours; split '%(name)s' per day.",
                    name=activity.name))
