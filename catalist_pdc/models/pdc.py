# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from datetime import date


class AccountJournalPdc(models.Model):
    _inherit = 'account.journal'


class AccountPaymentPdc(models.Model):
    _inherit = 'account.payment'
    _description = 'Account Payment'

    cheque_status = fields.Selection([('accepted', 'Accepted'), ('bounced', 'Bounced')],
                                     string='Cheque Status')
    journal_cheque_compute = fields.Char(string='Journal_id', compute='_compute_journal_cheque')
    cheque_dates = fields.Date(string='Cheque Date', default=date.today())
    cheque_nos = fields.Char(string='Cheque No.')

    # @api.depends('journal_id')
    # def _compute_date_and_no(self):
    #     data = self.env['account.payment.register'].search([])
    #     for dat in data:
    #         self.cheque_nos = dat.cheque_no
    #         self.cheque_dates = dat.cheque_date

    @api.depends('journal_id')
    def _compute_journal_cheque(self):
        for rec in self.journal_id:
            if rec.name == 'Cheque':
                self.journal_cheque_compute = 'cheque'
            elif rec.name != 'Cheque':
                self.journal_cheque_compute = 'not_cheque'

    def cheque_bounce(self):
        self.action_draft()
        self.action_cancel()
        if self.state == 'cancel':
            self.cheque_status = 'bounced'

    def after_confirm(self):
        self.cheque_status = 'accepted'
        if self.state != 'posted':
            self.action_post()
        elif self.state == 'posted':
            self.state = 'posted'

    def cheque_accept(self):
        return {
                'name': _('Account PDC Wizard'),
                'res_model': 'account.pdc',
                'view_mode': 'form',
                'context': {
                    'default_account_payment_id': self.id,
                },
                'target': 'new',
                'type': 'ir.actions.act_window',
                }

    def auto_mail(self):
        data = self.env['account.payment'].search([('journal_id.name', '=', 'Cheque')])
        for rec in data:
            if rec.cheque_dates == date.today():
                template = self.env.ref(
                    'catalist_pdc.pdc_mail_template',
                    raise_if_not_found=False)
                if template:
                    email_values = {
                        'email_to': rec.create_uid.email,
                    }
                    template.send_mail(
                        rec.id, email_values=email_values,
                        notif_layout='mail.mail_notification_light')


class AccountPaymentRegister(models.TransientModel):
    _inherit = 'account.payment.register'

    cheque_date = fields.Date(string='Cheque Date', store=True, default=date.today())
    cheque_no = fields.Char(string='Cheque No.', store=True)
    journal_cheque_payment_compute = fields.Char(string='Journal_id', compute='_compute_payment_journal_cheque')
    account_move_id = fields.Many2one('account.move')

    @api.depends('journal_id')
    def _compute_payment_journal_cheque(self):
        if self.journal_id.name == 'Cheque':
            self.journal_cheque_payment_compute = 'cheque'
        elif self.journal_id.name != 'Cheque':
            self.journal_cheque_payment_compute = 'not_cheque'

    def _create_payment_vals_from_wizard(self):
        if self.journal_id.name == 'Cheque':
            cheque_no = self.cheque_no
            cheque_date = self.cheque_date
        else:
            cheque_no = False
            cheque_date = False
        payment_vals = {
            'date': self.payment_date,
            'cheque_dates': cheque_date,
            'cheque_nos': cheque_no,
            'amount': self.amount,
            'payment_type': self.payment_type,
            'partner_type': self.partner_type,
            'ref': self.communication,
            'journal_id': self.journal_id.id,
            'currency_id': self.currency_id.id,
            'partner_id': self.partner_id.id,
            'partner_bank_id': self.partner_bank_id.id,
            'payment_method_id': self.payment_method_id.id,
            'destination_account_id': self.line_ids[0].account_id.id
        }

        if not self.currency_id.is_zero(self.payment_difference) and self.payment_difference_handling == 'reconcile':
            payment_vals['write_off_line_vals'] = {
                'name': self.writeoff_label,
                'amount': self.payment_difference,
                'account_id': self.writeoff_account_id.id,
            }
        return payment_vals

    def _create_payment_vals_from_batch(self, batch_result):
        batch_values = self._get_wizard_values_from_batch(batch_result)
        return {
            'date': self.payment_date,
            'amount': batch_values['source_amount_currency'],
            'payment_type': batch_values['payment_type'],
            'partner_type': batch_values['partner_type'],
            'ref': self._get_batch_communication(batch_result),
            'journal_id': self.journal_id.id,
            'currency_id': batch_values['source_currency_id'],
            'partner_id': batch_values['partner_id'],
            'partner_bank_id': batch_result['key_values']['partner_bank_id'],
            'payment_method_id': self.payment_method_id.id,
            'destination_account_id': batch_result['lines'][0].account_id.id
        }
