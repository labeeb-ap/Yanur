from odoo import models, fields, _


class AccountMove(models.Model):
    _inherit = "account.move"

    journal_branch_transfer_id = fields.Many2one('journal.branch.transfer', string='Journal Branch Transfer')


class AccountAccount(models.Model):
    _inherit = 'account.account'

    company_name = fields.Char(related='company_id.name', string='Company Name', store=True)
    account_type_id = fields.Many2one('account.account', string="Account")
