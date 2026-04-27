from odoo import fields, models, api


class Company(models.Model):
    _inherit = 'res.company'

    control_acc_id = fields.Many2one('account.account', string='Control Account')
