from odoo import fields, api, models, _
from odoo.exceptions import ValidationError
from datetime import datetime, date


class HrLeaveEncashmentPayment(models.Model):
    _name = 'hr.leave.encashment.payment'
    _inherit = ['mail.thread']
    _order = 'name desc'

    employee_id = fields.Many2one('hr.employee', string='Employee', required=True)
    department_id = fields.Many2one('hr.department', string="Department", related="employee_id.department_id",
                                    store=True)
    job_id = fields.Many2one('hr.job', string="Job", related="employee_id.job_id", store=True)
    manager_id = fields.Many2one('res.users', string="Manager", related="employee_id.parent_id.user_id", store=True)
    current_user = fields.Many2one('res.users', string="Current User", related='employee_id.user_id',
                                   default=lambda self: self.env.uid, store=True)
    name = fields.Char('Name', readonly=True, copy=False)
    # project_id = fields.Many2one('project.project', string="Project")
    # project_manager_id = fields.Many2one('res.users', string="Project Manager")
    contract_id = fields.Many2one('hr.contract', string="Contract")
    note = fields.Text(string='Note')
    state = fields.Selection([('draft', 'Draft'),
                              ('waiting', 'Waiting'),
                              ('approved', 'Approved'),
                              ('posted', 'Posted'),
                              ('refused', 'Refused'), ('cancel', 'Cancelled')], string="Status",
                             default="draft")
    debit_account_id = fields.Many2one('account.account', string='Debit Account')
    credit_account_id = fields.Many2one('account.account', string='Credit Account')
    journal_id = fields.Many2one('account.journal', string='Journal')
    user_id = fields.Many2one('res.users', string='User', readonly=True, default=lambda self: self.env.user.id)
    company_id = fields.Many2one('res.company', string='Company', readonly=True,
                                 default=lambda self: self.env.company.id)
    date = fields.Date(string='Date', readonly=True, default=date.today())
    leave_encashment_req = fields.Many2one('hr.leave.encashment', string='Leave Encashment Request', copy=False)
    encashment_amount_total = fields.Float(string='Total Encashment Amount', copy=False)
    encashment_amount_balance = fields.Float(string='Total Encashment Amount Balance', copy=False)
    amount_to_post = fields.Float(string='Amount to Post', copy=False)

    @api.onchange('employee_id')
    def _onchange_employee_id(self):
        self.contract_id = False
        if self.employee_id:
            if self.employee_id.contract_ids:
                for co in self.employee_id.contract_ids:
                    if co.state == 'close':
                        self.contract_id = co.id
                        self.job_id = co.job_id
                        print(self.contract_id)
            else:
                self.contract_id = False


    @api.model
    def create(self, vals):
        if vals.get('name', _('New')) == _('New'):
            vals['name'] = self.env['ir.sequence'].next_by_code('hr.leave.encashment.payment') or _('New')
        res = super(HrLeaveEncashmentPayment, self).create(vals)
        return res

    def encashment_submit(self):
        if self.leave_encashment_req:
                if self.amount_to_post > self.encashment_amount_balance:
                    raise ValidationError(
                        "Can't give a greater value for 'Amount to Post' than 'Total Encashment Amount Balance'")
        self.state = 'waiting'
        print(self.amount_to_post,self.encashment_amount_balance)


    def encashment_approve(self):
        self.state = 'approved'

    def encashment_post(self):
        if self.employee_id.user_id:
            if self.debit_account_id and self.credit_account_id and self.journal_id:
                journal_entry = self.env['account.move'].create({
                    'ref': self.name,
                    'move_type': 'entry',
                    'journal_id': self.journal_id.id,
                    'company_id': self.company_id.id,
                    'currency_id': self.company_id.currency_id.id,
                    'payment_reference': self.name,
                    'date': self.date,
                    'line_ids': [
                        (0, 0, {
                            'account_id': self.credit_account_id.id,
                            'currency_id': self.company_id.currency_id.id,
                            'debit': 00.0,
                            'credit': round(self.amount_to_post),
                            'partner_id': self.employee_id.user_id.partner_id.id,
                        }),
                        (0, 0, {
                            'account_id': self.debit_account_id.id,
                            'currency_id': self.company_id.currency_id.id,
                            'debit': round(self.amount_to_post),
                            'credit': 0.0,
                            'partner_id': self.employee_id.user_id.partner_id.id,
                        }),
                    ],
                })
                journal_entry.action_post()

            else:
                raise ValidationError('Debit Account , Credit Account and Journal must be selected')
        else:
            raise ValidationError("Please set a 'Related User' for the employee")
        self.leave_encashment_req.encashment_amount_balance -= self.amount_to_post
        self.leave_encashment_req.is_not_paid = False
        self.state = 'posted'

    def encashment_refused(self):
        self.state = 'refused'

    def encashment_reset_draft(self):
        self.state = 'draft'

    def encashment_cancel(self):
        self.state = 'cancel'

    @api.onchange('leave_encashment_req')
    def _onchange_leave_encashment_req(self):
        if self.leave_encashment_req:
            self.encashment_amount_total = self.leave_encashment_req.encashment_amount_total
            self.encashment_amount_balance = self.leave_encashment_req.encashment_amount_balance



