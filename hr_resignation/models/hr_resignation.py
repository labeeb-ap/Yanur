import datetime
from datetime import datetime, timedelta
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

date_format = "%Y-%m-%d"
RESIGNATION_TYPE = [('resigned', 'Normal Resignation'),
                    ('fired', 'Fired by the company')]


class HrResignation(models.Model):
    _name = 'hr.resignation'
    _inherit = 'mail.thread'
    _rec_name = 'employee_id'

    name = fields.Char(string='Reference', required=True, copy=False, readonly=True, index=True,
                       default=lambda self: _('New'))
    employee_id = fields.Many2one('hr.employee', string="Employee", default=lambda self: self.env.user.employee_id.id)
    department_id = fields.Many2one('hr.department', string="Department", related='employee_id.department_id')
    resign_confirm_date = fields.Date(string="Confirmed Date", track_visibility="always")
    approved_revealing_date = fields.Date(string="Approved Last Day Of Employee",
                                          help='Date on which the request is confirmed by the manager.',
                                          track_visibility="always")
    joined_date = fields.Date(string="Join Date", store=True)

    expected_revealing_date = fields.Date(string="Last Day of Employee", required=True)
    reason = fields.Text(string="Reason", required=True, help='Specify reason for leaving the company')
    notice_period = fields.Integer(string="Notice Period")
    state = fields.Selection(
        [('draft', 'Draft'), ('confirm', 'Confirm'), ('approved', 'Approved'), ('cancel', 'Rejected'),
         ('clearance', 'Clearance')],
        string='Status', default='draft', track_visibility="always")
    resignation_type = fields.Selection(selection=RESIGNATION_TYPE, help="Select the type of resignation: normal"
                                                                         "resignation or fired by the company")
    read_only = fields.Boolean(string="check field")
    employee_contract = fields.Char(String="Contract")

    exit_clear_count_total = fields.Integer(string='Total', readonly="True", store=True,
                                            compute='_compute_exit_clearance_count')

    def _compute_exit_clearance_count(self):
        for i in self:
            count = self.env['employee.exit.clearance'].sudo().search(
                [('resignation_id', '=', i.id),
                 ('employee_id', '=', i.employee_id.id)])
            i.exit_clear_count_total = len(count)

    # @api.onchange('employee_id')
    # def set_join_date(self):
    #     # self.joined_date = self.employee_id.joining_date if self.employee_id.joining_date else ''
    #     self.joined_date = self.employee_id.joining_date

    # @api.depends('employee_id')
    # def compute_join_date(self):
    #     # self.joined_date = self.employee_id.joining_date if self.employee_id.joining_date else ''
    #     if employee_id.joining_date :
    #         self.joined_date = self.employee_id.joining_date
    #     else :
    #         self.joined_date = False

    @api.model
    def create(self, vals):
        # assigning the sequence for the record
        if vals.get('name', _('New')) == _('New'):
            vals['name'] = self.env['ir.sequence'].next_by_code('hr.resignation') or _('New')
        res = super(HrResignation, self).create(vals)
        return res

    @api.constrains('employee_id')
    def check_employee(self):
        # Checking whether the user is creating leave request of his/her own
        for rec in self:
            if not self.env.user.has_group('hr.group_hr_user'):
                if rec.employee_id.user_id.id != self.env.user.id:
                    raise ValidationError(_('You cannot create request for other employees'))

    @api.onchange('employee_id')
    def check_request_existence(self):
        # Check whether any resignation request already exists
        self.employee_contract = False
        self.notice_period = False
        self.joined_date = False
        for rec in self:
            if rec.employee_id.contract_id:
                if rec.employee_id.contract_id.state == 'open':
                    rec.employee_contract = rec.employee_id.contract_id.name
                    rec.notice_period = rec.employee_id.contract_id.notice_days
            rec.joined_date = rec.employee_id.joining_date

    @api.constrains('joined_date', 'employee_id')
    def _check_dates(self):
        # validating the entered dates
        for rec in self:
            resignation_request = self.env['hr.resignation'].sudo().search([('employee_id', '=', rec.employee_id.id),
                                                                            ('state', 'in', ['confirm', 'approved'])])
            if resignation_request:
                raise ValidationError(
                    _('There is a resignation request in confirmed or approved state for this employee'))

    def confirm_resignation(self):
        if self.joined_date:
            if self.joined_date >= self.expected_revealing_date:
                raise ValidationError(_('Last date of the Employee must be anterior to Joining date'))
            for rec in self:
                rec.state = 'confirm'
                rec.resign_confirm_date = str(datetime.now())
        else:
            raise ValidationError(_('Please set joining date for employee'))

    def cancel_resignation(self):
        for rec in self:
            rec.state = 'cancel'

    def reject_resignation(self):
        for rec in self:
            rec.state = 'cancel'

    def reset_to_draft(self):
        for rec in self:
            rec.state = 'draft'
            rec.employee_id.active = True
            rec.employee_id.resigned = False
            rec.employee_id.fired = False

    def approve_resignation(self):
        exit = self.env['employee.exit.clearance'].sudo().search(
            [('resignation_id', '=', self.id), ('employee_id', '=', self.employee_id.id)])
        for i in exit:
            if i.state != 'approved':
                raise ValidationError(_("Exit Clearance Not Approved"))
        for rec in self:
            if rec.expected_revealing_date and rec.resign_confirm_date:
                no_of_contract = self.env['hr.contract'].search([('employee_id', '=', rec.employee_id.id)])
                for contracts in no_of_contract:
                    if contracts.state == 'open':
                        rec.employee_contract = contracts.name
                        rec.state = 'approved'
                        rec.approved_revealing_date = rec.resign_confirm_date + timedelta(days=contracts.notice_days)
                    else:
                        rec.approved_revealing_date = rec.expected_revealing_date
                # Changing state of the employee if resigning today
                if rec.expected_revealing_date <= fields.Date.today() and rec.employee_id.active:
                    rec.employee_id.active = False
                    # Changing fields in the employee table with respect to resignation
                    rec.employee_id.resign_date = rec.expected_revealing_date
                    if rec.resignation_type == 'resigned':
                        rec.employee_id.resigned = True
                    else:
                        rec.employee_id.fired = True
                    # Removing and deactivating user
                    if rec.employee_id.user_id:
                        rec.employee_id.user_id.active = False
                        rec.employee_id.user_id = None
            else:
                raise ValidationError(_('Please enter valid dates.'))

    def update_employee_status(self):
        resignation = self.env['hr.resignation'].search([('state', '=', 'approved')])
        for rec in resignation:
            if rec.expected_revealing_date <= fields.Date.today() and rec.employee_id.active:
                rec.employee_id.active = False
                # Changing fields in the employee table with respect to resignation
                rec.employee_id.resign_date = rec.expected_revealing_date
                if rec.resignation_type == 'resigned':
                    rec.employee_id.resigned = True
                else:
                    rec.employee_id.fired = True
                # Removing and deactivating user
                if rec.employee_id.user_id:
                    rec.employee_id.user_id.active = False
                    rec.employee_id.user_id = None

    def button_settlement(self):
        if self.employee_id.resignation_department_ids:
            if len(self.employee_id.resignation_department_ids) > 0:
                for i in self.employee_id.resignation_department_ids:
                    self.env['employee.exit.clearance'].create({
                        'resig_department_id': i.id,
                        'user_id': i.approved_user_id.id,
                        'employee_id': self.employee_id.id,
                        'last_day': self.expected_revealing_date,
                        'notice_period': self.notice_period,
                        'reason': self.reason,
                        'resignation_id': self.id,
                    })
                self._compute_exit_clearance_count()
        self.state = 'clearance'

    def action_exit_clearance_records(self):
        return {
            'type': 'ir.actions.act_window',
            'name': 'Exit Clearance',
            'res_model': 'employee.exit.clearance',
            'view_mode': 'tree,form',
            'domain': [('resignation_id', '=', self.id),
                       ('employee_id', '=', self.employee_id.id)],
            'context': {'create': False, 'delete': False},
        }


class HrEmployee(models.Model):
    _inherit = 'hr.employee'

    resign_date = fields.Date('Resign Date', readonly=True, help="Date of the resignation")
    resigned = fields.Boolean(string="Resigned", default=False, store=True,
                              help="If checked then employee has resigned")
    fired = fields.Boolean(string="Fired", default=False, store=True, help="If checked then employee has fired")
