from odoo import fields, models


class ResCompany(models.Model):
    _inherit = 'res.company'

    maintenance_labour_rate = fields.Monetary(
        string='Default Labour Rate',
        currency_field='currency_id',
        default=0.0,
        help="Hourly labour rate used on maintenance activities when the "
             "technician has no hourly cost defined on their employee record.",
    )
    maintenance_warranty_alert_days = fields.Integer(
        string='Warranty Alert (Days)',
        default=30,
        help="Equipment whose warranty expires within this number of days "
             "is flagged as 'Expiring Soon'.",
    )
