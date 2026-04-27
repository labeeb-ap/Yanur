from odoo import models, fields, _


class AccountJournal(models.Model):
    _inherit = "account.journal"

    is_inter_branch = fields.Boolean(string='Is Inter Branch')


class AccountMove(models.Model):
    _inherit = "account.move"

    inter_branch_ref = fields.Char(string='Internal Reference')
    remarks = fields.Text(string='Remarks')
