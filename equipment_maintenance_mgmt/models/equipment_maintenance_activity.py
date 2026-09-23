from odoo import api, fields, models
from odoo.exceptions import ValidationError


class EquipmentMaintenanceActivity(models.Model):
    _name = 'equipment.maintenance.activity'
    _description = 'Maintenance Activity'
    _inherit = ['equipment.maintenance.line.mixin']
    _order = 'date desc, id'

    def _default_technician_id(self):
        """Default to the technician of the request, else the current user."""
        request_id = self.env.context.get('default_request_id')
        if request_id:
            request = self.env['equipment.maintenance.request'].browse(request_id)
            if request.technician_id:
                return request.technician_id
        return self.env.user

    name = fields.Char(string='Activity Description', required=True)
    technician_id = fields.Many2one(
        'res.users', string='Technician', required=True, index=True,
        default=_default_technician_id)
    date = fields.Date(string='Date', required=True, default=fields.Date.context_today)
    hours_spent = fields.Float(string='Hours Spent', required=True, default=1.0)
    labour_rate = fields.Monetary(
        string='Labour Rate', currency_field='currency_id',
        compute='_compute_labour_rate', store=True, readonly=False, precompute=True,
        help="Hourly rate. Defaults to the hourly cost of the technician's employee, "
             "otherwise to the default labour rate of the company.")
    cost = fields.Monetary(
        string='Cost', currency_field='currency_id',
        compute='_compute_cost', store=True, aggregator='sum')

    _hours_spent_positive = models.Constraint(
        'CHECK(hours_spent > 0)', 'Hours spent must be greater than zero.')
    _labour_rate_positive = models.Constraint(
        'CHECK(labour_rate >= 0)', 'The labour rate cannot be negative.')

    @api.depends('technician_id', 'request_id.company_id')
    def _compute_labour_rate(self):
        for activity in self:
            company = activity.request_id.company_id or self.env.company
            # hourly_cost is restricted to HR officers (groups="hr.group_hr_user"):
            # read it with sudo, only the resulting rate is exposed on the line.
            employee = activity.technician_id.sudo().with_company(company).employee_id
            activity.labour_rate = employee.hourly_cost or company.maintenance_labour_rate

    @api.depends('hours_spent', 'labour_rate')
    def _compute_cost(self):
        # Labour cost of one activity line = hours spent x hourly labour rate
        for activity in self:
            activity.cost = activity.hours_spent * activity.labour_rate

    @api.constrains('hours_spent')
    def _check_hours_spent(self):
        for activity in self:
            if activity.hours_spent > 24:
                raise ValidationError(self.env._(
                    "An activity line cannot exceed 24 hours; split '%(name)s' per day.",
                    name=activity.name))
