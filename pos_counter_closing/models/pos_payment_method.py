from odoo import api, fields, models, _
from odoo.exceptions import ValidationError

class PosPaymentMethod(models.Model):
    _inherit = 'pos.payment.method'

    main_account_id = fields.Many2one('account.account', string='Main Account')
    closing_account_id = fields.Many2one('account.account', string='Counter Closing Account')
    profit_account_id = fields.Many2one('account.account', string='Profit Account')
    loss_account_id = fields.Many2one('account.account', string='Loss Account')
    journal_id = fields.Many2one('account.journal', string='Journal')
    account_type = fields.Selection([('cash', 'Cash'), ('bank', 'Bank Transfer'),('card', 'Card'),('cheque', 'Cheque'),('discount', 'Discount'),('voucher', 'Voucher')], string='Type')

    # account_id = fields.Many2one('account.account', default=lambda self: self._default_account())
    #
    # def _default_account(self):
    #     # Find and return the desired default account record
    #     account = self.env['account.account'].search([('account_type', '=', 'discount')], limit=1)
    #     return account

# class PosPayment(models.Model):
#     _inherit = 'pos.payment'
#
#     account_id = fields.Many2one('account.account', default=lambda self: self._default_account())
#
#     def _default_account(self):
#         # Find and return the desired default account record
#         account = self.env['account.account'].search([('account_type', '=', 'discount')], limit=1)
#         return account
#




