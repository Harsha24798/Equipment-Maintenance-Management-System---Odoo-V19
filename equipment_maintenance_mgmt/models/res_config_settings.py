from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    maintenance_currency_id = fields.Many2one(
        'res.currency', related='company_id.currency_id', string='Maintenance Currency')
    maintenance_labour_rate = fields.Monetary(
        related='company_id.maintenance_labour_rate',
        currency_field='maintenance_currency_id',
        readonly=False,
    )
    maintenance_warranty_alert_days = fields.Integer(
        related='company_id.maintenance_warranty_alert_days',
        readonly=False,
    )
