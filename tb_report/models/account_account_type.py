from odoo import fields, models


class AccountAccountType(models.Model):
    _inherit = 'account.account.type'

    type_order = fields.Integer(string='Type Code', default=1, store=True)
