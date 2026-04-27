from odoo import models, fields, _


class AccountAccount(models.Model):
    _inherit = "account.account"

    control_code = fields.Char(string='Control Code')
