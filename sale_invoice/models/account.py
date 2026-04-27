from odoo import models, fields, api, _
import num2words


class AccountMoveReport(models.Model):
    _inherit = 'account.move'

    amount_in_words = fields.Char(string='Amount In Words', compute='_compute_total_amount_in_words')

    @api.depends('amount_total')
    def _compute_total_amount_in_words(self):
        currency = 'Rupees'  # Replace with your desired currency name

        for record in self:
            if record.amount_total:
                amount_in_words = num2words.num2words(record.amount_total, lang='en').title()
                record.amount_in_words = f"{amount_in_words} {currency}"
            else:
                record.amount_in_words = False

class ResPartnerInherit(models.Model):
    _inherit = 'res.company'

    acc_bank_name = fields.Char(string='Bank Name')
    # bank_branch = fields.Char(string='Bank Branch')
    acc_number = fields.Char(string='Account Number')