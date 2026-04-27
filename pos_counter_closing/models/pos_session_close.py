from odoo import api, fields, models, _
from odoo.exceptions import ValidationError
from datetime import datetime, date


class PossSessionClose(models.Model):
    _name = 'pos.session.close'
    _description = 'Pos Session Close'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    # _rec_name = 'value'

    session_ids = fields.Many2many('pos.session', string='Sessions')
    state = fields.Selection([('draft', 'Draft'), ('done', 'Closed')], default='draft', tracking=True)
    date = fields.Date('Date')
    cash_line_ids = fields.One2many('pos.cash.close.line', 'session_close_id', string="Cash Line ids", tracking=True)
    payment_line_ids = fields.One2many('pos.close.other.payment.line', 'session_close_id',
                                       string="other Payment Line ids", tracking=True)
    float_cash = fields.Float('Float Cash', tracking=True)
    close_at = fields.Datetime('Closed Time')
    active = fields.Boolean('Active', default=True)
    company_id = fields.Many2one('res.company', string='Company', index=True, default=lambda self: self.env.company.id)
    # user_id = fields.Many2one('res.users', string='Company', index=True, default=lambda self: self.env.user)
    # company_id = fields.Many2one('res.company', string='Company', index=True)
    cash_difference = fields.Float(string='Cash Difference', tracking=True)
    move_id = fields.Many2one('account.move', string='Entry')
    cash_details = fields.Many2one('pos.order', string='Pos')
    account_id = fields.Many2one('account.account', string='Account', default=lambda self: self._default_account())
    debit_amount = fields.Float(string='Debit Amount', compute='_compute_debit_amount', store=True)

    def _default_account(self):
        account = self.env['account.account'].search([('account_type', '=', 'voucher')], limit=1)
        return account

    @api.depends('account_id', 'date')
    def _compute_debit_amount(self):
        for record in self:
            debit_amount = 0.0
            if record.account_id and record.date:
                move_line = self.env['account.move.line'].search([
                    ('account_id', '=', record.account_id.id),
                    ('debit', '>', 0.0),
                    ('date', '=', record.date),
                ], limit=1)
                debit_amount = move_line.debit if move_line else 0.0
            record.debit_amount = debit_amount

    def get_sale_details(self):
        if self.date:
            user = self.env.user.id
            x = self.date.strftime('%Y-%m-%d 00:00:00')
            y = self.date.strftime('%Y-%m-%d 23:59:59')

            company_id = self.company_id.id

            self.env.cr.execute(('''SELECT
                                    po.date_order as OrderDate,
                                    SUM(CASE WHEN ppm.account_type = 'cash' THEN pp.amount ELSE 0 END) AS Cash,
                                    SUM(CASE WHEN ppm.account_type = 'bank' THEN pp.amount ELSE 0 END) AS Bank,
                                    SUM(CASE WHEN ppm.account_type = 'card' THEN pp.amount ELSE 0 END) AS Card,
                                    COUNT(DISTINCT po.pos_reference) AS order,
                                    COUNT(pp.payment_method_id) as payment,
                                    COUNT(CASE WHEN ppm.account_type = 'cash' THEN pp.payment_method_id END) AS cash_payment,
                                    COUNT(CASE WHEN ppm.account_type = 'bank' THEN pp.payment_method_id END) AS bank_payment,
                                    COUNT(CASE WHEN ppm.account_type = 'card' THEN pp.payment_method_id END) AS card_payment,
                                    SUM(CASE WHEN ppd.default_code = 'DISC' THEN (pol.price_unit * pol.qty) ELSE 0 END) AS total_discount
                                    FROM pos_payment AS pp
                                    LEFT JOIN pos_payment_method AS ppm ON pp.payment_method_id = ppm.id
                                    LEFT JOIN pos_order AS po ON pp.pos_order_id = po.id
                                    LEFT JOIN pos_order_line AS pol ON pol.order_id = po.id
                                    LEFT JOIN product_product AS ppd ON pol.product_id = ppd.id
                                    WHERE po.date_order AT TIME ZONE 'UTC' BETWEEN '%s' AND '%s'
                                    AND po.company_id = %s
                                    GROUP BY OrderDate
                                      ''') % (x, y, company_id))
            move_ids = self.env.cr.dictfetchall()

            result_dict = {}
            for dict_item in move_ids:
                for key, value in dict_item.items():
                    if key in result_dict:
                        if isinstance(result_dict[key], (int, float)):
                            result_dict[key] += value
                        else:
                            result_dict[key] = value
                    else:
                        result_dict[key] = value

            return result_dict

    def update_company(self):
        sessions = self.env['pos.session.close'].sudo().search([])
        for session in sessions:
            if session.sudo().session_ids:
                a = session.session_ids.sudo().mapped('company_id')
                session.company_id = a
            # company_id = session.session_ids.mapped('company_id'):
            # for s in session.session_ids:
            #     session.company_id = s.company_id.id

    def action_close_pos_session(self):
        session_name = self.session_ids.mapped('name')
        if self.payment_line_ids:
            for other_payment_line in self.payment_line_ids:
                ledger_ids = self.env['account.move.line'].search([('parent_state', '=', 'posted'),
                                                                   ('account_id', '=',
                                                                    other_payment_line.payment_method_id.main_account_id.id)])
                balance = sum(ledger_ids.mapped('balance'))
                print('other_payment_line.amount', other_payment_line.amount)
                final = other_payment_line.amount - balance
                other_payment_line.difference = final
                if final > 0:
                    move_id = self.env['account.move'].sudo().create({
                        'journal_id': other_payment_line.payment_method_id.journal_id.id,
                        'move_type': 'entry',
                        'date': self.date,
                        'ref': session_name,
                    })
                    move_id.write({'line_ids': [(0, 0,
                                                 {
                                                     'account_id': other_payment_line.payment_method_id.closing_account_id.id,
                                                     'name': session_name,
                                                     'debit': other_payment_line.amount, 'credit': 0, }),
                                                (0, 0,
                                                 {'account_id': other_payment_line.payment_method_id.main_account_id.id,
                                                  'name': 'Counter Closing',
                                                  'debit': 0, 'credit': balance, }),
                                                (0, 0,
                                                 {
                                                     'account_id': other_payment_line.payment_method_id.profit_account_id.id,
                                                     'name': session_name,
                                                     'debit': 0, 'credit': final, })
                                                ]})
                    move_id.action_post()
                    other_payment_line.move_id = move_id.id
                if final < 0:
                    move_id = self.env['account.move'].sudo().create({
                        'journal_id': other_payment_line.payment_method_id.journal_id.id,
                        'move_type': 'entry',
                        'date': self.date,
                        'ref': session_name,
                    })
                    move_id.write({'line_ids': [(0, 0,
                                                 {
                                                     'account_id': other_payment_line.payment_method_id.closing_account_id.id,
                                                     'name': session_name,
                                                     'debit': other_payment_line.amount, 'credit': 0, }),
                                                (0, 0,
                                                 {'account_id': other_payment_line.payment_method_id.main_account_id.id,
                                                  'name': 'Counter Closing',
                                                  'debit': 0, 'credit': balance, }),
                                                (0, 0,
                                                 {'account_id': other_payment_line.payment_method_id.loss_account_id.id,
                                                  'name': session_name,
                                                  'debit': - final, 'credit': 0, })
                                                ]})
                    move_id.action_post()
                    other_payment_line.move_id = move_id.id

                if final == 0:
                    if other_payment_line.amount != 0:
                        move_id = self.env['account.move'].sudo().create({
                            'journal_id': other_payment_line.payment_method_id.journal_id.id,
                            'move_type': 'entry',
                            'date': self.date,
                            'ref': session_name,
                        })
                        move_id.write({'line_ids': [
                            (0, 0,
                             {'account_id': other_payment_line.payment_method_id.main_account_id.id,
                              'name': 'Counter Closing',
                              'debit': 0, 'credit': other_payment_line.amount, }),
                            (0, 0,
                             {'account_id': other_payment_line.payment_method_id.closing_account_id.id,
                              'name': session_name,
                              'debit': other_payment_line.amount, 'credit': 0, })
                        ]})
                        move_id.action_post()
                        other_payment_line.move_id = move_id.id

        cash_pos_payment_method_id = self.env['pos.payment.method'].search([('is_credit', '=', False),
                                                                            ('is_cash_count', '=', True)], limit=1)
        cash_ledger_ids = self.env['account.move.line'].search([('parent_state', '=', 'posted'),
                                                                ('account_id', '=',
                                                                 cash_pos_payment_method_id.main_account_id.id)])
        cash_balance = sum(cash_ledger_ids.mapped('balance'))
        if cash_balance < 0:
            raise ValidationError(_('Your Cash Balance is Negative!!!'))
        cash_total = sum(self.cash_line_ids.mapped('amount'))
        cash = cash_total
        if cash < 0:
            raise ValidationError(_('Float Cash should be LessThan or EqualTo Total Cash'))

        cash_final = cash - cash_balance
        ##cash difference
        self.cash_difference = cash_final
        ##
        if cash_final != 0:
            if cash_final > 0:
                move_id = self.env['account.move'].sudo().create({
                    'journal_id': cash_pos_payment_method_id.journal_id.id,
                    'move_type': 'entry',
                    'date': self.date,
                    'ref': session_name,
                })

                move_id.write({'line_ids': [(0, 0,
                                             {'account_id': cash_pos_payment_method_id.closing_account_id.id,
                                              'name': session_name,
                                              'move_id': move_id.id,
                                              'debit': cash, 'credit': 0, }),
                                            (0, 0,
                                             {'account_id': cash_pos_payment_method_id.main_account_id.id,
                                              'name': 'Counter Closing',
                                              'move_id': move_id.id,
                                              'debit': 0, 'credit': cash_balance}),
                                            (0, 0,
                                             {'account_id': cash_pos_payment_method_id.profit_account_id.id,
                                              'name': session_name,
                                              'move_id': move_id.id,
                                              'debit': 0, 'credit': cash_final, })
                                            ]})

                move_id.action_post()
                self.move_id = move_id.id
            if cash_final < 0:
                move_id = self.env['account.move'].sudo().create({
                    'journal_id': cash_pos_payment_method_id.journal_id.id,
                    'move_type': 'entry',
                    'date': self.date,
                    'ref': session_name,
                })
                move_id.write({'line_ids': [(0, 0,
                                             {'account_id': cash_pos_payment_method_id.closing_account_id.id,
                                              'name': session_name,
                                              'debit': cash, 'credit': 0, }),
                                            (0, 0,
                                             {'account_id': cash_pos_payment_method_id.main_account_id.id,
                                              'name': 'Counter Closing',
                                              'debit': 0, 'credit': cash_balance, }),
                                            (0, 0,
                                             {'account_id': cash_pos_payment_method_id.loss_account_id.id,
                                              'name': session_name,
                                              'debit': - cash_final, 'credit': 0, })
                                            ]})
                move_id.action_post()
                self.move_id = move_id.id
        if cash_final == 0:
            move_id = self.env['account.move'].sudo().create({
                'journal_id': cash_pos_payment_method_id.journal_id.id,
                'move_type': 'entry',
                'date': self.date,
                'ref': session_name,
            })
            move_id.write({'line_ids': [
                (0, 0,
                 {'account_id': cash_pos_payment_method_id.main_account_id.id,
                  'name': 'Counter Closing',
                  'debit': 0, 'credit': cash, }),
                (0, 0,
                 {'account_id': cash_pos_payment_method_id.closing_account_id.id,
                  'name': session_name,
                  'debit': cash, 'credit': 0, }),

            ]})
            move_id.action_post()
            self.move_id = move_id.id

        if self.float_cash > 0:
            move_id = self.env['account.move'].sudo().create({
                'journal_id': cash_pos_payment_method_id.journal_id.id,
                'move_type': 'entry',
                'date': self.date,
                'ref': session_name,
            })
            move_id.write({'line_ids': [(0, 0,
                                         {'account_id': cash_pos_payment_method_id.closing_account_id.id,
                                          'name': session_name,
                                          'debit': 0, 'credit': self.float_cash, }),
                                        (0, 0,
                                         {'account_id': cash_pos_payment_method_id.main_account_id.id,
                                          'name': session_name,
                                          'debit': self.float_cash, 'credit': 0, }),
                                        ]})
            move_id.action_post()
            self.move_id = move_id.id
        self.close_at = datetime.now()
        self.state = 'done'


class PosCashClosingLine(models.Model):
    _name = 'pos.cash.close.line'

    session_close_id = fields.Many2one('pos.session.close', string='Session Close')
    count = fields.Integer(string='Count')
    currency_type = fields.Float(string='Currency')
    amount = fields.Float(string='Total Amount')

    @api.onchange('count', 'currency_type')
    def _onchange_amount_total(self):
        if self.currency_type:
            self.amount = self.count * self.currency_type


class PosCloseOtherPaymentLine(models.Model):
    _name = 'pos.close.other.payment.line'

    session_close_id = fields.Many2one('pos.session.close', string='Session Close')
    amount = fields.Float(string='Amount')
    payment_method_id = fields.Many2one('pos.payment.method', string='Payment Method',
                                        domain="['|', ('is_cash_count', '!=', 'true'), ('is_credit', '=', 'true')]")
    move_id = fields.Many2one('account.move', string='Entry')
    difference = fields.Float(string='Difference', tracking=True)
    # currency_type =

#
# class PossSessionCloseUser(models.Model):
#     _inherit = 'res.user'
