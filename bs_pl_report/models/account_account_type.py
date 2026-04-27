from odoo import models, fields


class AccountAccountType(models.Model):
    _inherit = 'account.account.type'

    report_group = fields.Selection([
        ('income', 'Income'),
        ('cost_of_revenue', 'Cost Of Revenue')], string="Report Group", store=True)
