from odoo import fields, models


class ResCompany(models.Model):
    """Extend the standard company with maintenance settings."""
    # _inherit without _name: add fields to the EXISTING model res.company
    # (classic inheritance, no new table)
    _inherit = 'res.company'

    # Fallback hourly rate for technicians without an employee hourly cost
    maintenance_labour_rate = fields.Monetary(
        string='Default Labour Rate',
        currency_field='currency_id',
        default=0.0,
        help="Hourly labour rate used on maintenance activities when the "
             "technician has no hourly cost defined on their employee record.",
    )
    # Used by equipment.warranty_state to flag "Expiring Soon"
    maintenance_warranty_alert_days = fields.Integer(
        string='Warranty Alert (Days)',
        default=30,
        help="Equipment whose warranty expires within this number of days "
             "is flagged as 'Expiring Soon'.",
    )
