from odoo import api, fields, models, _


class AccountAccount(models.Model):
    _inherit = 'account.account'

    closing_type = fields.Selection([('cash_sale', 'Cash Sale'),
                                     ('card_sale', 'Card Sale'),
                                     ('credit_sale', 'Credit Sale'),
                                     ('cash_diff', 'Cash Difference'),
                                     ('card_diff', 'Card Difference'),
                                     ('credit_diff', 'Credit Difference')
                                     ])

    account_type = fields.Selection([('cash', 'Cash'), ('bank', 'Bank Transfer'),('card', 'Card'),('cheque', 'Cheque'),('discount', 'Discount'),('voucher', 'Voucher'),('stakeholders', 'Stakeholders'),('Accounts', 'Accounts'),('hr', 'HR'),('operation', 'Operation'),('general', 'General')], string='Amount Type')



class AccountJournal(models.Model):
    _inherit = 'account.journal'

    is_credit = fields.Boolean(string='Is Credit')
    default_account_id = fields.Many2one(comodel_name='account.account', check_company=True, copy=False,
                                         ondelete='restrict', string='Default Account', domain="")


class PosPaymentMethod(models.Model):
    _inherit = 'pos.payment.method'

    is_credit = fields.Boolean(string='Is Credit', related='cash_journal_id.is_credit', readonly=False)

class AccountPax(models.Model):
    _inherit = "account.move"

    pax_qty = fields.Integer(string="Pax")
