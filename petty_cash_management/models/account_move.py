from odoo import models, fields, _


class AccountMove(models.Model):
    _inherit = "account.move"

    petty_cash_id = fields.Many2one('petty.cash.management', string='Petty Cash')

    def button_cancel(self):
        res = super(AccountMove, self).button_cancel()
        if self.petty_cash_id:
            self.petty_cash_id.action_cancel()
        return res