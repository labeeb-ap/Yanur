from odoo import fields, models


class account_field(models.Model):
    _inherit = 'account.account'

    cash_flow = fields.Boolean(string='Cash Flow')