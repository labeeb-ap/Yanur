from calendar import monthrange

from odoo import fields, api, models, _
from odoo.exceptions import ValidationError
from datetime import datetime, date


class HrLeaveEncashment(models.Model):
    _name = 'hr.leave.encashment'
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
    debit_account_id = fields.Many2one('account.account', string='Debit Account', copy=False)
    credit_account_id = fields.Many2one('account.account', string='Credit Account', copy=False)
    journal_id = fields.Many2one('account.journal', string='Journal', copy=False)
    user_id = fields.Many2one('res.users', string='User', readonly=True, default=lambda self: self.env.user.id)
    company_id = fields.Many2one('res.company', string='Company', readonly=True,
                                 default=lambda self: self.env.company.id)
    date = fields.Date(string='Date', readonly=True, default=date.today())
    accounting_date = fields.Date(string='Accounting Date')
    leave_type_id = fields.Many2one('hr.leave.type', string='Leave type', copy=False)
    no_of_days_left = fields.Float(string='No of days', copy=False)
    no_of_days_encash = fields.Float(string='No of days to Encash', copy=False)
    amount_per_day = fields.Float(string='Amount per Day')
    encashment_amount_total = fields.Float(string='Total Encashment Amount', copy=False, store=True)
    encashment_amount_balance = fields.Float(string='Balance Amount', copy=False, store=True)
    is_not_paid = fields.Boolean(string='Not Paid', compute='compute_state')
    is_partial_paid = fields.Boolean(string='Partial Paid', compute='compute_state')
    is_fully_paid = fields.Boolean(string='Paid', compute='compute_state')
    is_posted = fields.Boolean(string='posted')

    @api.onchange('employee_id', 'no_of_days_encash', 'leave_type_id')
    def _onchange_employee_id(self):
        self.no_of_days_left = False
        self.amount_per_day = False
        self.encashment_amount_total = False
        day = 0
        encashment = 0
        # self.project_id = False
        if self.employee_id:
            if self.employee_id.contract_ids:
                for co in self.employee_id.contract_ids:
                    if co.state == 'close':
                        self.contract_id = co.id
                        self.job_id = co.job_id
                        dates = self.date
                        month_range = monthrange(dates.year, dates.month)[1]
                        print(month_range)
                        amt = (co.wage / month_range)
                        self.amount_per_day = amt

            else:
                self.contract_id = False
                self.amount_per_day = 0.00
        # else:
        #     self.contract_id = False
        #     self.amount_per_day = 0.00
        if self.contract_id and self.amount_per_day:
            amts = self.amount_per_day * self.no_of_days_encash
            self.encashment_amount_total = amts
            encashment = self.encashment_amount_total
        else:
            self.encashment_amount_total = 0.00
            encashment = self.encashment_amount_total
        print(encashment)
        if self.leave_type_id and self.employee_id and self.employee_id.contract_ids:
            left_days = self.env['hr.leave.report'].search(
                [('employee_id', '=', self.employee_id.id), ('state', '=', 'validate'),
                 ('holiday_status_id.active', '=', True), ('holiday_status_id', '=', self.leave_type_id.id)])
            left_holiday = 0
            for left in left_days:
                left_holiday += left.number_of_days
            self.no_of_days_left = left_holiday

    @api.model
    def create(self, vals):
        if vals.get('name', _('New')) == _('New'):
            vals['name'] = self.env['ir.sequence'].next_by_code('hr.leave.encashment') or _('New')
        res = super(HrLeaveEncashment, self).create(vals)
        return res

    def encashment_submit(self):
        self.state = 'waiting'

    def encashment_approve(self):
        # if self.leave_type_id:
        #     leave = self.env['hr.leave'].create({
        #         'employee_id': self.employee_id.id,
        #         'department_id': self.department_id.id,
        #         # 'category_id': self.department_id.id,
        #         'mode_company_id': self.company_id.id,
        #         'holiday_status_id': self.leave_type_id.id,
        #         'number_of_days': self.no_of_days_encash,
        #         'name': 'Encashment of %s' % self.name
        #     })
        #     leave.action_approve()
        #     leave.action_validate()
        self.encashment_amount_balance = round(self.encashment_amount_total)
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
                    'invoice_date': self.accounting_date,
                    'line_ids': [
                        (0, 0, {
                            'account_id': self.credit_account_id.id,
                            'currency_id': self.company_id.currency_id.id,
                            'debit': 00.0,
                            'credit': round(self.encashment_amount_total),
                            'partner_id': self.employee_id.user_id.partner_id.id,
                        }),
                        (0, 0, {
                            'account_id': self.debit_account_id.id,
                            'currency_id': self.company_id.currency_id.id,
                            'debit': round(self.encashment_amount_total),
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

        self.is_posted = True
        self.state = 'posted'

    def encashment_refused(self):
        self.state = 'refused'

    def encashment_reset_draft(self):
        self.state = 'draft'

    def encashment_cancel(self):
        self.state = 'cancel'

    @api.depends('encashment_amount_total', 'encashment_amount_balance', 'state')
    def compute_state(self):
        for i in self:
            if i.state == 'posted':
                print(i.encashment_amount_total)
                print(i.encashment_amount_balance)
                if round(i.encashment_amount_total) == i.encashment_amount_balance:
                    i.is_not_paid = True
                    i.is_partial_paid = False
                    i.is_fully_paid = False
                elif i.encashment_amount_balance == 0.0:
                    i.is_not_paid = False
                    i.is_partial_paid = False
                    i.is_fully_paid = True
                elif i.encashment_amount_total > i.encashment_amount_balance:
                    i.is_not_paid = False
                    i.is_partial_paid = True
                    i.is_fully_paid = False
                else:
                    i.is_not_paid = False
                    i.is_partial_paid = False
                    i.is_fully_paid = False
            else:
                i.is_not_paid = False
                i.is_partial_paid = False
                i.is_fully_paid = False
