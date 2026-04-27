from odoo import api, fields, models, _
from odoo.exceptions import ValidationError
from datetime import date

class PosSession(models.Model):
    _inherit = 'pos.session'

    cash_line_ids = fields.One2many('pos.cash.line', 'session_id', string="Cash Line ids")
    payment_line_ids = fields.One2many('pos.other.payment.line', 'session_id', string="other Payment Line ids")
    is_add_cash_closing = fields.Boolean('Cash closing', default=False)
    float_cash = fields.Float('Float Cash')
    cash_sale = fields.Float('Cash Sale')
    card_sale = fields.Float('Card Sale')
    credit_sale = fields.Float('Credit Sale')


    def add_currency_type(self):
        currency_type_ids = self.env['currency.type'].search([])
        for currency_type_id in currency_type_ids:
            self.write({'cash_line_ids': [(0, 0,
                                           {'currency_type': currency_type_id.value})
                                          ]})
        payment_method_ids = self.env['pos.payment.method'].search([])
        for payment_method_id in payment_method_ids:
            if (payment_method_id.is_cash_count and payment_method_id.is_credit) or \
                    (not payment_method_id.is_cash_count and not payment_method_id.is_credit):
                self.write({'payment_line_ids': [(0, 0,
                                                  {'payment_method_id': payment_method_id.id})
                                                 ]})
        self.is_add_cash_closing = True

    def _check_pos_session_balance(self):
        res = super(PosSession, self)._check_pos_session_balance()
        # cash sale
        cash_sale_ledger_ids = self.env['account.move.line'].search([('parent_state', '=', 'posted'),
                                                                     ('date', '=', date.today()),
                                                                     ('account_id.closing_type', '=', 'cash_sale'
                                                                      )])
        # cash_date = cash_sale_ledger_ids.filtered(lambda m: m.date == self.stop_at.date())
        cash_sale_balance = sum(cash_sale_ledger_ids.mapped('balance'))
        if self.cash_sale == 0:
            self.cash_sale = cash_sale_balance
        #card sale
        card_sale_ledger_ids = self.env['account.move.line'].search([('parent_state', '=', 'posted'),
                                                                     ('date', '=', date.today()),
                                                                     ('account_id.closing_type', '=', 'card_sale'
                                                                      )])
        card_sale_balance = sum(card_sale_ledger_ids.mapped('balance'))

        if self.card_sale == 0:
            self.card_sale = card_sale_balance

        # credit sale
        credit_sale_ledger_ids = self.env['account.move.line'].search([('parent_state', '=', 'posted'),
                                                                       ('date', '=', date.today()),
                                                                       ('account_id.closing_type', '=', 'credit_sale'
                                                                        )])
        credit_sale_balance = sum(credit_sale_ledger_ids.mapped('balance'))
        if self.credit_sale == 0:
            self.credit_sale = credit_sale_balance

        return res
    def action_pos_session_closing_control(self):
        res = super(PosSession, self).action_pos_session_closing_control()
        mail_user = self.config_id.mail_user_id
        pos_order_ids = self.env['pos.order'].search([('session_id', '=', self.id)])
        move_ids = self.env['account.move'].search([('invoice_date', '=', self.stop_at.date()),
                                                    ('move_type', '=', 'out_invoice'), ('state', '=', 'posted'),
                                                    ('payment_state', '!=', 'reversed')])
        pos_cash_total = sum(pos_order_ids.mapped('amount_total'))
        move_cash_total = sum(move_ids.mapped('amount_total_signed'))
        payment_sum = sum(self.payment_line_ids.mapped('amount'))
        #cash sale
        # cash_sale_ledger_ids = self.env['account.move.line'].search([
        #                                                              ('parent_state', '=', 'posted'),
        #                                                              # ('date', '=', self.stop_at.date()),
        #                                                              ('account_id.closing_type', '=', 'cash_sale'
        #                                                               )])
        cash_sale_ledger_ids = self.env['account.move.line'].search([('parent_state', '=', 'posted'),
                                                                     ('date', '=', date.today()),
                                                                     ('account_id.closing_type', '=', 'cash_sale'
                                                                      )])
        cash_sale_balance = sum(cash_sale_ledger_ids.mapped('balance'))
        #card sale
        card_sale_ledger_ids = self.env['account.move.line'].search([('parent_state', '=', 'posted'),
                                                                     ('date', '=', self.stop_at.date()),
                                                                     ('account_id.closing_type', '=', 'card_sale'
                                                                      )])
        card_sale_balance = sum(card_sale_ledger_ids.mapped('balance'))
        #credit sale
        credit_sale_ledger_ids = self.env['account.move.line'].search([('parent_state', '=', 'posted'),
                                                                     ('date', '=', self.stop_at.date()),
                                                                     ('account_id.closing_type', '=', 'credit_sale'
                                                                      )])
        credit_sale_balance = sum(credit_sale_ledger_ids.mapped('balance'))
            # raise ValidationError(_("yes"))
        # if not mail_user:
        #     raise ValidationError(_("Please set a mail user in session settings."))
        # if not self.cash_line_ids and not self.payment_line_ids:
        #     raise ValidationError(_("Please Add Cash closing line"))
        pos_payment_ids = self.env['pos.payment'].search([('session_id', '=', self.id),
                                                          ('payment_method_id.is_cash_count', '=', False)])
        payment_methods = pos_payment_ids.mapped('payment_method_id')
        if payment_methods:
            for payment_method in payment_methods:
                payment_line = pos_payment_ids.filtered(lambda m: m.payment_method_id == payment_method)
                payment_sum = sum(payment_line.mapped('amount'))
                move_id = self.env['account.move'].sudo().create({
                    'journal_id': payment_method.journal_id.id,
                    'move_type': 'entry',
                    'date': self.stop_at.date(),
                    'ref': self.name,
                })
                move_id.write({'line_ids': [(0, 0,
                                             {'account_id': payment_method.receivable_account_id.id,
                                              'name': self.name,
                                              'debit': 0, 'credit': payment_sum, }),
                                            (0, 0,
                                             {'account_id': payment_method.main_account_id.id,
                                              'name': self.name,
                                              'debit': payment_sum, 'credit': 0, })
                                            ]})
                move_id.action_post()
        # if self.payment_line_ids:
        #     for other_payment_line in self.payment_line_ids:
        #         ledger_ids = self.env['account.move.line'].search([('parent_state', '=', 'posted'),
        #             ('account_id', '=', other_payment_line.payment_method_id.main_account_id.id)])
        #         balance = sum(ledger_ids.mapped('balance'))
        #         final = other_payment_line.amount - balance
        #         if final > 0:
        #             move_id = self.env['account.move'].sudo().create({
        #                 'journal_id': other_payment_line.payment_method_id.journal_id.id,
        #                 'move_type': 'entry',
        #                 'date': self.stop_at.date(),
        #                 'ref': self.name,
        #             })
        #             move_id.write({'line_ids': [(0, 0,
        #                                          {'account_id': other_payment_line.payment_method_id.closing_account_id.id,
        #                                           'name': self.name,
        #                                           'debit': other_payment_line.amount, 'credit': 0, }),
        #                                         (0, 0,
        #                                          {'account_id': other_payment_line.payment_method_id.main_account_id.id,
        #                                           'name': self.name,
        #                                           'debit': 0, 'credit': balance, }),
        #                                         (0, 0,
        #                                          {'account_id': other_payment_line.payment_method_id.profit_account_id.id,
        #                                           'name': self.name,
        #                                           'debit': 0, 'credit': final, })
        #                                         ]})
        #             move_id.action_post()
        #
        #         if final < 0:
        #             move_id = self.env['account.move'].sudo().create({
        #                 'journal_id': other_payment_line.payment_method_id.journal_id.id,
        #                 'move_type': 'entry',
        #                 'date': self.stop_at.date(),
        #                 'ref': self.name,
        #             })
        #             move_id.write({'line_ids': [(0, 0,
        #                                          {'account_id': other_payment_line.payment_method_id.closing_account_id.id,
        #                                           'name': self.name,
        #                                           'debit': other_payment_line.amount, 'credit': 0, }),
        #                                         (0, 0,
        #                                          {'account_id': other_payment_line.payment_method_id.main_account_id.id,
        #                                           'name': self.name,
        #                                           'debit': 0, 'credit': balance, }),
        #                                         (0, 0,
        #                                          {'account_id': other_payment_line.payment_method_id.loss_account_id.id,
        #                                           'name': self.name,
        #                                           'debit': - final, 'credit': 0, })
        #                                         ]})
        #             move_id.action_post()
        #
        # cash_pos_payment_method_id = self.env['pos.payment.method'].search([('is_credit', '=', False),
        #                                                   ('is_cash_count', '=', True)], limit=1)
        # cash_ledger_ids = self.env['account.move.line'].search([('parent_state', '=', 'posted'),
        #                                                    ('account_id', '=',
        #                                                     cash_pos_payment_method_id.main_account_id.id)])
        # cash_balance = sum(cash_ledger_ids.mapped('balance'))
        #
        # cash_total = sum(self.cash_line_ids.mapped('amount'))
        # cash = cash_total
        # if cash < 0:
        #     raise ValidationError(_('Float Cash should be LessThan or EqualTo total Cash'))
        # cash_final = cash - cash_balance
        #
        # if cash_final != 0:
        #     if cash_final > 0:
        #         move_id = self.env['account.move'].sudo().create({
        #             'journal_id': cash_pos_payment_method_id.journal_id.id,
        #             'move_type': 'entry',
        #             'date': self.stop_at.date(),
        #             'ref': self.name,
        #         })
        #         move_id.write({'line_ids': [(0, 0,
        #                                      {'account_id': cash_pos_payment_method_id.closing_account_id.id,
        #                                       'name': self.name,
        #                                       'debit': cash, 'credit': 0, }),
        #                                     (0, 0,
        #                                      {'account_id': cash_pos_payment_method_id.main_account_id.id,
        #                                       'name': self.name,
        #                                       'debit': 0, 'credit': cash_balance, }),
        #                                     (0, 0,
        #                                      {'account_id': cash_pos_payment_method_id.profit_account_id.id,
        #                                       'name': self.name,
        #                                       'debit': 0, 'credit': cash_final, })
        #                                     ]})
        #         move_id.action_post()
        #     if cash_final < 0:
        #         move_id = self.env['account.move'].sudo().create({
        #             'journal_id': cash_pos_payment_method_id.journal_id.id,
        #             'move_type': 'entry',
        #             'date': self.stop_at.date(),
        #             'ref': self.name,
        #         })
        #         move_id.write({'line_ids': [(0, 0,
        #                                      {'account_id': cash_pos_payment_method_id.closing_account_id.id,
        #                                       'name': self.name,
        #                                       'debit': cash, 'credit': 0, }),
        #                                     (0, 0,
        #                                      {'account_id': cash_pos_payment_method_id.main_account_id.id,
        #                                       'name': self.name,
        #                                       'debit': 0, 'credit': cash_balance, }),
        #                                     (0, 0,
        #                                      {'account_id': cash_pos_payment_method_id.loss_account_id.id,
        #                                       'name': self.name,
        #                                       'debit': - cash_final, 'credit': 0, })
        #                                     ]})
        #         move_id.action_post()
        # if self.float_cash > 0:
        #     move_id = self.env['account.move'].sudo().create({
        #         'journal_id': cash_pos_payment_method_id.journal_id.id,
        #         'move_type': 'entry',
        #         'date': self.stop_at.date(),
        #         'ref': self.name,
        #     })
        #     move_id.write({'line_ids': [(0, 0,
        #                                  {'account_id': cash_pos_payment_method_id.closing_account_id.id,
        #                                   'name': self.name,
        #                                   'debit': 0, 'credit': self.float_cash, }),
        #                                 (0, 0,
        #                                  {'account_id': cash_pos_payment_method_id.main_account_id.id,
        #                                   'name': self.name,
        #                                   'debit': self.float_cash, 'credit': 0, }),
        #                                 ]})
        #     move_id.action_post()
        #cash diff
        cash_diff_ledger_ids = self.env['account.move.line'].search([('parent_state', '=', 'posted'),
                                                                     ('date', '=', self.stop_at.date()),
                                                                     ('account_id.closing_type', '=', 'cash_diff'
                                                                      )])
        cash_diff_balance = sum(cash_diff_ledger_ids.mapped('balance'))
        # card diff
        card_diff_ledger_ids = self.env['account.move.line'].search([('parent_state', '=', 'posted'),
                                                                     ('date', '=', self.stop_at.date()),
                                                                     ('account_id.closing_type', '=', 'card_diff'
                                                                      )])
        card_diff_balance = sum(card_diff_ledger_ids.mapped('balance'))
        # credit diff
        credit_diff_ledger_ids = self.env['account.move.line'].search([('parent_state', '=', 'posted'),
                                                                       ('date', '=', self.stop_at.date()),
                                                                       (
                                                                       'account_id.closing_type', '=', 'credit_diff'
                                                                       )])
        credit_diff_balance = sum(credit_diff_ledger_ids.mapped('balance'))
        #customer order
        order_ids = self.env['sale.order'].search([('state', 'not in', ('draft', 'sent', 'cancel'))])
        order_count = 0
        # for order_id in order_ids:
        #     if order_id.date_order.date() == self.stop_at.date():
        #         order_count += 1
        home_del_count = self.env['account.move'].search_count([('invoice_date', '=', self.stop_at.date()),
                                                                ('move_type', '=', 'out_invoice'),
                                                                # ('home_delivery_inv', '=', 'true'),
                                                                ('payment_state', '!=', 'reversed'),
                                                                ('state', '=', 'posted')])
        ##<mail
        cst = self.cash_sale - cash_sale_balance
        if mail_user:
            mail_values = {
                'subject': "Counter Closing mail",
                # 'email_from': j.department_id,
                'email_to': mail_user.partner_id.email,
                'body_html': "<style> .mt1 {border: 1px solid black; border-collapse: collapse;}, th, td {padding-right: 3px;}</style>"
                             "<div><h3 align=center>COUNTER CLOSING REPORT - %s</h3>"
                             "<table style='border: 1px solid black; border-collapse: collapse;' align='center' cellspacing='10' class='mt1'><thead>"
                             "<tr><th style='border: 1px solid black; border-collapse: collapse;' class='mt1'><span> Location <span/></th><td style='border: 1px solid black; border-collapse: collapse;' class='mt1'><span> %s<span/></td></tr>"
                             "<tr><th style='border: 1px solid black; border-collapse: collapse;' class='mt1'><span> Closing Time<span/></th><td style='border: 1px solid black; border-collapse: collapse;' class='mt1'><span> %s<span/></td></tr>"
                             "<tr><th style='border: 1px solid black; border-collapse: collapse;' class='mt1'><span> Total Sale<span/></th><td style='border: 1px solid black; border-collapse: collapse;' class='mt1'><span> %s<span/></td></tr>"
                             "<tr><th style='border: 1px solid black; border-collapse: collapse;' class='mt1'><span> Cash Sale<span/></th><td style='border: 1px solid black; border-collapse: collapse;' class='mt1'><span> %s<span/></td></tr>"
                             "<tr><th style='border: 1px solid black; border-collapse: collapse;' class='mt1'><span> Card Sale<span/></th><td style='border: 1px solid black; border-collapse: collapse;' class='mt1'><span> %s<span/></td></tr>"
                             "<tr><th style='border: 1px solid black; border-collapse: collapse;' class='mt1'><span> Credit Sale<span/></th><td style='border: 1px solid black; border-collapse: collapse;' class='mt1'><span> %s<span/></td></tr>"
                             "<tr><th style='border: 1px solid black; border-collapse: collapse;' class='mt1'><span> Cash Difference<span/></th><td style='border: 1px solid black; border-collapse: collapse;' class='mt1'><span> %s<span/></td></tr>"
                             "<tr><th style='border: 1px solid black; border-collapse: collapse;' class='mt1'><span> Card Difference<span/></th><td style='border: 1px solid black; border-collapse: collapse;' class='mt1'><span> %s<span/></td></tr>"
                             "<tr><th style='border: 1px solid black; border-collapse: collapse;' class='mt1'><span> Credit Difference<span/></th><td style='border: 1px solid black; border-collapse: collapse;' class='mt1'><span> %s<span/></td></tr>"
                             "<tr><th style='padding-top: 20px; class='mt1'><span></span></th><td style='padding-top: 20px; class='mt1'><span></span></td></tr>"
                             "<tr><th style='border: 1px solid black; border-collapse: collapse;' class='mt1'><span> Customer Order Received<span/></th><td style='border: 1px solid black; border-collapse: collapse;' class='mt1'><span> %s<span/></td></tr>"
                             "<tr><th style='border: 1px solid black; border-collapse: collapse;' class='mt1'><span> Home Delivery Count  <span/></th><td style='border: 1px solid black; border-collapse: collapse;' class='mt1'><span> %s<span/></td></tr>"
                             "</thead></table></div>" % (self.name, self.env.company.name, self.stop_at, pos_cash_total+move_cash_total, self.cash_sale, self.card_sale, self.credit_sale, cash_diff_balance, card_diff_balance, credit_diff_balance, order_count, home_del_count),
                'auto_delete': False,
            }
            mail = self.env['mail.mail'].sudo().create(mail_values)
            mail.send(raise_exception=False)
        # x = self.env['pos.order'].search([('state','=','paid')])
        # print(x,'fghjk')
        # if x.state == 'paid':
        #     raise UserWarning('Close the session After creating manufacturing entry')
        return res


class PosClosingLine(models.Model):
    _name = 'pos.cash.line'

    session_id = fields.Many2one('pos.session', string='Session')
    count = fields.Integer(string='Count')
    currency_type = fields.Float(string='Currency')
    amount = fields.Float(string='Total Amount')

    @api.onchange('count', 'currency_type')
    def _onchange_amount_total(self):
        if self.currency_type:
            self.amount = self.count * self.currency_type



class PosOtherPaymentLine(models.Model):
    _name = 'pos.other.payment.line'

    session_id = fields.Many2one('pos.session', string='Session')
    amount = fields.Integer(string='Amount')
    payment_method_id = fields.Many2one('pos.payment.method', string='Payment Method',
                                        domain="['|', ('is_cash_count', '!=', 'true'), ('is_credit', '=', 'true')]")
    # currency_type =

