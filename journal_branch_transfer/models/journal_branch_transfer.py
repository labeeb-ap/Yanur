from odoo import models, fields, api, _
from datetime import date
from odoo.exceptions import UserError


class JournalBranchTransfer(models.Model):
    _name = "journal.branch.transfer"
    _description = 'Journal Branch Transfer'
    _rec_name = 'name'

    name = fields.Char(string='Doc No.', default='/')
    remarks = fields.Text(string='Remarks')
    date = fields.Date(string='Date', default=date.today())
    state = fields.Selection([('draft', 'Draft'), ('confirm', 'Confirmed'), ('done', 'Posted')], string='State',
                             default='draft')
    line_ids = fields.One2many('journal.branch.transfer.line', 'journal_branch_id', string='Line ids')
    partner_id = fields.Many2one('res.partner', string='Partner')
    company_id = fields.Many2one('res.company', string='Company', required=True, default=lambda self: self.env.company)
    account_id = fields.Many2one('account.account', string='Account', required=True,
                                 domain="[('company_id', '=', company_id),('control_code','=',False)]")
    journal_id = fields.Many2one('account.journal', store=True, readonly=False, required=True,
                                 domain="[('company_id', '=', company_id),('is_inter_branch', '=', True)]")

    reference = fields.Char(string='Reference No')
    total = fields.Float(string="Total", compute='compute_total', store=True, tracking=True)

    @api.depends('line_ids.debit')
    def compute_total(self):
        for ln in self:
            ln.total = 0
            for line in ln.line_ids:
                if line.debit:
                    ln.total += line.debit


    @api.model
    def default_get(self, fields_list):
        defaults = super(JournalBranchTransfer, self).default_get(fields_list)

        journal = self.env['account.journal'].search([
            ('is_inter_branch', '=', True),
            ('company_id', '=', defaults.get('company_id', False))
        ], limit=1)

        defaults['journal_id'] = journal.id if journal else False
        return defaults

    # journal_id = fields.Many2one('account.journal', store=True, readonly=False, required=True,
    #                              domain="[('company_id', '=', company_id), ('type', 'in', ('bank', 'cash'))]")

    @api.model
    def create(self, vals):
        if vals.get('name', 'New') != '/':
            # vals['name'] = self.env['ir.sequence'].next_by_code('journal.branch.transfer') or _('New')
            vals['name'] = '/'
        result = super(JournalBranchTransfer, self).create(vals)
        return result

    def action_confirm(self):
        if self.name == '/':
            self.name = self.env['ir.sequence'].next_by_code('journal.branch.transfer') or _('New')
        if not self.line_ids:
            raise UserError(
                _("You need to add a line before Confirm."))
        for line in self.line_ids:
            if line.credit and line.debit:
                raise UserError(
                    _("You can't add debit and credit in a single line."))

        self.state = 'confirm'

    def reset_draft(self):
        self.state = 'draft'

    def create_journal_multi(self):
        for line in self.line_ids:
            company = self.env['res.company'].sudo().search([('id', '=', line.company_id.id)])
            move_id = self.env['account.move'].sudo().create({
                'journal_id': line.journal_id.id,
                'company_id': company.id,
                'move_type': 'entry',
                'date': self.date,
                'ref': self.name,
                'state': 'draft',
                'journal_branch_transfer_id': self.id,
                'partner_id': line.partner_id.id,
                'inter_branch_ref': self.reference,
                'remarks': self.remarks
            })

            move_id.sudo().update({
                'journal_id': line.journal_id.id,
                'company_id': line.company_id.id,
            })
            account_id = self.env['account.account'].sudo().search(
                [('control_code', '=', self.company_id.control_acc_id.control_code),
                 ('company_id', '=', company.id)], limit=1)
            if not account_id:
                raise UserError(
                    _("Control code not set properly."))
            else:
                move_id.write({'line_ids': [(0, 0,
                                             {'account_id': line.account_id.id, 'partner_id': line.partner_id.id,
                                              'name': line.name,
                                              'debit': line.debit, 'credit': line.credit, }),
                                            (0, 0,
                                             {'account_id': account_id.id, 'partner_id': line.partner_id.id,
                                              'name': line.name,
                                              'debit': line.credit, 'credit': line.debit, })
                                            ]})

            # current company
            current_move_id = self.env['account.move'].sudo().create({
                'journal_id': self.journal_id.id,
                'company_id': self.company_id.id,
                'move_type': 'entry',
                'date': self.date,
                'ref': self.name,
                'state':'draft',
                'journal_branch_transfer_id': self.id,
                'partner_id': line.partner_id.id,
                'inter_branch_ref': self.reference,
                'remarks': self.remarks
            })
            current_account_id = self.env['account.account'].sudo().search(
                [('control_code', '=', company.control_acc_id.control_code),
                 ('company_id', '=', self.company_id.id)], limit=1)
            if not account_id:
                raise UserError(
                    _("Control code not set properly."))
            else:
                current_move_id.write({'line_ids': [(0, 0,
                                                     {'account_id': self.account_id.id,
                                                      'partner_id': line.partner_id.id,
                                                      'name': line.name,
                                                      'debit': line.credit, 'credit': line.debit, }),
                                                    (0, 0,
                                                     {'account_id': current_account_id.id,
                                                      'partner_id': line.partner_id.id,
                                                      'name': line.name,
                                                      'debit': line.debit, 'credit': line.credit, })
                                                    ]})
            # current_move_id.action_post()

        self.state = 'done'


class JournalBranchTransferLine(models.Model):
    _name = "journal.branch.transfer.line"
    _description = 'Journal Branch Transfer Lines'

    name = fields.Char(string='Label')
    account_id = fields.Many2one('account.account', string='Account', required=True)
    company_id = fields.Many2one('res.company', string='Company', required=True)
    currency_id = fields.Many2one(related='company_id.currency_id')
    debit = fields.Monetary(string='Debit')
    credit = fields.Monetary(string='Credit')
    partner_id = fields.Many2one('res.partner', string='Partner')
    journal_branch_id = fields.Many2one('journal.branch.transfer')
    control_account_id = fields.Many2one(related='company_id.control_acc_id')
    journal_id = fields.Many2one('account.journal', store=True, readonly=False, required=True,
                                 domain="[('company_id', '=', company_id),('is_inter_branch', '=', True)]")

    @api.onchange('company_id')
    def _onchange_company_id(self):
        if self.company_id:
            journal = self.env['account.journal'].search([
                ('is_inter_branch', '=', True),
                ('company_id', '=', self.company_id.id)
            ], limit=1)
            self.journal_id = journal.id if journal else False

    #
    # @api.model
    # def default_journal(self):
    #     journal = self.env['account.journal'].search([('is_inter_branch', '=', True)], limit=1)
    #     return journal and journal.id
    # journal_id = fields.Many2one('account.journal', store=True, readonly=False, required=True,
    #                              domain="[('company_id', '=', company_id), ('type', 'in', ('bank', 'cash'))]")
