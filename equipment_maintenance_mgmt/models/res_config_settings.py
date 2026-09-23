from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    """Settings screen (Configuration > Settings) of the maintenance app."""
    # TransientModel: temporary records (the settings wizard), cleaned automatically
    _inherit = 'res.config.settings'

    # Dedicated currency field for the monetary setting below
    maintenance_currency_id = fields.Many2one(
        'res.currency', related='company_id.currency_id', string='Maintenance Currency')
    # related + readonly=False: saving the settings writes the value on the company
    maintenance_labour_rate = fields.Monetary(
        related='company_id.maintenance_labour_rate',
        currency_field='maintenance_currency_id',
        readonly=False,
    )
    maintenance_warranty_alert_days = fields.Integer(
        related='company_id.maintenance_warranty_alert_days',
        readonly=False,
    )
