# -*- coding: utf-8 -*-

from odoo import models, fields


class AccountSelect(models.TransientModel):
    _name = 'account.pdc'
    _description = "Account Select"

    account_id = fields.Many2one('account.account', string='Select Account')
    account_payment_id = fields.Many2one('account.payment')
    date = fields.Date(string='Cleared Date')

    def action_confirm(self):
        if self.account_payment_id.partner_type == 'customer':
            entry_id = self.env['account.move'].create({
                # 'name': self.account_payment_id.name,
                # 'date': self.account_payment_id.date,
                'date': self.date,
                'currency_id': self.account_payment_id.currency_id.id,
                'ref': self.account_payment_id.ref,
                'l10n_in_reseller_partner_id': self.account_payment_id.l10n_in_reseller_partner_id,
                'l10n_in_gst_treatment': self.account_payment_id.partner_id.l10n_in_gst_treatment,
                'move_type': 'entry',
                # 'state': self.account_payment_id.state,
                # 'state': 'draft',
                'journal_id': self.account_payment_id.journal_id.id,
                'partner_id': self.account_payment_id.partner_id.id,
                'company_id': self.account_payment_id.company_id.id,
                'line_ids': [(0, 0, {
                    'date': self.date,
                    'name': self.account_payment_id.name or '/',
                    'debit': self.account_payment_id.amount,
                    'account_id': self.account_id.id,
                    'partner_id': self.account_payment_id.partner_id.id,
                }), (0, 0, {
                    'date': self.date,
                    'name': self.account_payment_id.name or '/',
                    'credit': self.account_payment_id.amount,
                    'account_id': self.account_payment_id.journal_id.payment_debit_account_id.id,
                    'partner_id': self.account_payment_id.partner_id.id,
                })]
            })
            entry_id.post()
            self.account_payment_id.after_confirm()

        if self.account_payment_id.partner_type == 'supplier':
            entry_id = self.env['account.move'].create({
                # 'name': self.account_payment_id.name,
                # 'date': self.account_payment_id.date,
                'date': self.date,
                'currency_id': self.account_payment_id.currency_id.id,
                'ref': self.account_payment_id.ref,
                'l10n_in_reseller_partner_id': self.account_payment_id.l10n_in_reseller_partner_id,
                'l10n_in_gst_treatment': self.account_payment_id.partner_id.l10n_in_gst_treatment,
                'move_type': 'entry',
                # 'state': self.account_payment_id.state,
                # 'state': 'draft',
                'journal_id': self.account_payment_id.journal_id.id,
                'partner_id': self.account_payment_id.partner_id.id,
                'company_id': self.account_payment_id.company_id.id,
                'line_ids': [(0, 0, {
                    'date': self.date,
                    'name': self.account_payment_id.name or '/',
                    'credit': self.account_payment_id.amount,
                    'account_id': self.account_id.id,
                    'partner_id': self.account_payment_id.partner_id.id,
                }), (0, 0, {
                    'date': self.date,
                    'name': self.account_payment_id.name or '/',
                    'debit': self.account_payment_id.amount,
                    'account_id': self.account_payment_id.journal_id.payment_credit_account_id.id,
                    'partner_id': self.account_payment_id.partner_id.id,
                })]
            })
            entry_id.post()
            self.account_payment_id.after_confirm()

