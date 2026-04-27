from odoo import api, fields, models, _
from odoo.exceptions import Warning, AccessError, UserError
from datetime import datetime, date


class PettyCashManagement(models.Model):
    _name = 'petty.cash.management'
    _description = 'Petty Cash Management'

    name = fields.Char(string='Sl No', required=True, default=lambda self: _('New'), copy=False)
    company_id = fields.Many2one('res.company', string='company', required=True, readonly=True)
    account_id = fields.Many2one('account.account', string='Account', required=True)
    petty_cash_lines_ids = fields.One2many('petty.cash.management.lines', 'ref_id')
    state = fields.Selection(
        [('draft', 'Draft'), ('confirm', 'Confirmed'),
         ('post', 'Posted'), ('cancel', 'Cancelled')],
        default='draft', string="Status")
    currency_id = fields.Many2one("res.currency", string="Currency", default=lambda self:
    self.env.user.company_id.currency_id.id, required=True, readonly=True)
    total = fields.Float(string="Total", compute='compute_total', store=True)
    date = fields.Date(string='Date', help='Select date here', default=fields.Date.context_today)
    journal_id = fields.Many2one('account.journal', store=True, readonly=False,
                                 domain="[('company_id', '=', company_id)]")
    move_id = fields.Many2one('account.move', string='Entry', copy=False)

    @api.onchange('account_id')
    def onchange_payment_type(self):
        self.journal_id = self.account_id.journal_id.id
        # account_type = self.env['account.account.type'].search([('internal_group', '=', 'asset'),('type','=','liquidity'),('include_initial_balance','=',True)])
        # list1 = []
        # for i in account_type:
        #     account = self.env['account.account'].search([('user_type_id.id', '=', i.id)])
        #     for j in account:
        #         list1.append(j.id)
        # return {'domain': {'account_id': [('id', 'in', list1)]}}

    @api.model
    def create(self, values):
        if values.get('name', _('New')) == _('New'):
            values['name'] = self.env['ir.sequence'].next_by_code(
                'petty.cash.management.Sequence') or _('New')
        res = super(PettyCashManagement, self).create(values)
        return res

    @api.depends('petty_cash_lines_ids.amount')
    def compute_total(self):
        for ln in self:
            ln.total = 0
            for line in ln.petty_cash_lines_ids:
                if line.amount:
                    ln.total += line.amount

    @api.model
    def default_get(self, fields):
        res = super(PettyCashManagement, self).default_get(fields)
        x = self.env.company.id
        res.update({
            'company_id': x,
        })
        return res

    def action_confirm(self):
        if not self.petty_cash_lines_ids:
            raise UserError(
                _("You need to add a line before Confirm."))
        self.state = 'confirm'

    def action_post(self):
        print(self.total, "total")
        line_ids = []
        move_dict = {
            'move_type': 'entry',
            'narration': self.name,
            'petty_cash_id': self.id,
            'ref': self.name,
            'journal_id': self.journal_id.id,
            'date': self.date,
        }
        total = sum(self.petty_cash_lines_ids.mapped('amount'))
        nar = self.petty_cash_lines_ids.mapped('narration')
        narration = self.petty_cash_lines_ids.mapped(lambda m: "%(narration)s," % {
            'narration': m.narration,
        })
        x = str(nar)
        x = x.replace("[", "", )
        x = x.replace("]", "")
        x = x.replace("'", "")

        total_credit_line = (0, 0, {
            # 'name': self.name + ':Petty Cash',
            'name': x,
            'account_id': self.account_id.id,
            'journal_id': self.journal_id.id,
            'date': self.date,
            'debit': 0.0,
            'credit': total,

        })
        line_ids.append(total_credit_line)

        for line in self.petty_cash_lines_ids:
            debit_line = (0, 0, {
                'name': line.narration,
                'account_id': line.account_id.id,
                'date': self.date,
                'debit': line.amount,
                'credit': 0.0,

            })
            line_ids.append(debit_line)
        move_dict['line_ids'] = line_ids
        move = self.env['account.move'].create(move_dict)
        move.action_post()
        self.write({'move_id': move.id})
        self.state = 'post'

    def action_cancel(self):
        self.state = 'cancel'

    def action_draft(self):
        self.state = 'draft'


class PettyCashManagementLines(models.Model):
    _name = 'petty.cash.management.lines'

    account_id = fields.Many2one('account.account', string="Account")
    amount = fields.Float(string="Amount")
    narration = fields.Char(string="Narration")
    ref_id = fields.Many2one('petty.cash.management')

    # @api.onchange('account_id')
    # def onchange_account_id(self):
    #     account_type = self.env['account.account.type'].search(
    #         [('internal_group', '=', 'asset'), ('type', '=', 'liquidity'), ('include_initial_balance', '=', True)])
    #     list2 = []
    #     for i in account_type:
    #         account = self.env['account.account'].search([('user_type_id.id', '=', i.id)])
    #         for j in account:
    #             list2.append(j.id)
    #     return {'domain': {'account_id': [('id', 'not in', list2)]}}
