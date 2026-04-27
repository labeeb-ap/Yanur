# -*- coding: utf-8 -*-
from odoo import models, fields, api, tools, _
from datetime import datetime, date
from calendar import monthrange
from odoo.exceptions import UserError


class HrPayslip(models.Model):
    _inherit = 'hr.payslip'

    salary_cut_first_month = fields.Float(string='Salary cutting', store=True)
    partial_paid_amount = fields.Float(string='Partially Paid Salary')
    salary_remaining = fields.Float(sting='Net Salary')
    salary_adjustment = fields.Float(string='Salary Adjustment')
    employee_code = fields.Char(related='contract_id.employee_code', string='Employee Code')
    pf_num = fields.Char(related='contract_id.pf_num', string='PF Number')
    esi_num = fields.Char(related='contract_id.esi_num', string='ESI Number')
    gmc_num = fields.Char(related='contract_id.gmc_num', string='GMC Number')
    salary_payment = fields.Float(string='Salary Paid')
    active = fields.Boolean('Active', default=True)
    total_days_of_month = fields.Integer(string='Total Days')
    actual_working_days = fields.Float(string='Actual Working Days')
    paid_time_off_days = fields.Float(string='Paid Time Off Days')
    unpaid_time_off_days = fields.Float(string='Unpaid Time Off Days')

    def compute_sheet(self):
        date_from = self.date_from
        date_to = self.date_to
        self.total_days_of_month = monthrange(date_from.year, date_from.month)[1]
        paid_time_off_ids = self.env['hr.leave'].search([('state', '=', 'validate'),
                                                         ('employee_id', '=', self.employee_id.id),
                                                         ('holiday_status_id.is_paid_time_off', '=', True)])
        total_paid_time_off_days = 0
        for paid_time_off_id in paid_time_off_ids:
            if paid_time_off_id.request_date_from.month == self.date_from.month and paid_time_off_id.request_date_from.year == self.date_from.year:
                if paid_time_off_id.request_unit_half:
                    total_paid_time_off_days += 0.5
                else:
                    days = (paid_time_off_id.request_date_to - paid_time_off_id.request_date_from).days + 1
                    total_paid_time_off_days += days
        #             print('days', days)
        # print('ttl', total_paid_time_off_days)
        self.paid_time_off_days = total_paid_time_off_days
        total_unpaid_time_off_days = 0
        unpaid_time_off_ids = self.env['hr.leave'].search([('state', '=', 'validate'),
                                                           ('employee_id', '=', self.employee_id.id),
                                                           ('holiday_status_id.is_unpaid_time_off', '=', True)])
        # print(unpaid_time_off_ids, 'unpaid_time_off_ids')
        for paid_time_off_id in unpaid_time_off_ids:
            if paid_time_off_id.request_date_from.month == self.date_from.month and paid_time_off_id.request_date_from.year == self.date_from.year:
                if paid_time_off_id.request_unit_half:
                    total_unpaid_time_off_days += 0.5
                else:
                    days = (paid_time_off_id.request_date_to - paid_time_off_id.request_date_from).days + 1
                    total_unpaid_time_off_days += days
        self.unpaid_time_off_days = total_unpaid_time_off_days
        ##attendance
        half_day_ids = self.env['hr.leave'].search([('state', '=', 'validate'),
                                                    ('employee_id', '=', self.employee_id.id),
                                                    ('request_unit_half', '!=', False)
                                                    ])
        attendance_ids = self.env['hr.attendance'].search([('employee_id', '=', self.employee_id.id)])
        half_att = 0
        for attendance_id in attendance_ids:
            if attendance_id.check_in.month == self.date_from.month and attendance_id.check_in.year == self.date_from.year:
                att = 0
                for half_day_id in half_day_ids:
                    # if half_day_id.request_date_from.month == self.date_from.month and half_day_id.request_date_from.year == self.date_from.year:

                    if half_day_id.request_date_from == attendance_id.check_in.date():
                        print(half_day_id.request_date_from, '==', attendance_id.check_in.date())
                        att += 0.5
                    # else:
                    #     att += 1
                    #     print('att', att)
                half_att += att
        total_att = 0
        for attendance_id in attendance_ids:
            if attendance_id.check_in.month == self.date_from.month and attendance_id.check_in.year == self.date_from.year:
                total_att += 1

        self.actual_working_days = total_att - half_att



        month_range = monthrange(date_to.year, date_to.month)[1]
        date_difference = (date_to - date_from).days + 1
        wage = self.contract_id.wage
        diff = month_range - date_difference
        one_day_wage = wage / month_range
        cut = one_day_wage * diff
        self.salary_cut_first_month = -cut

        res = super(HrPayslip, self).compute_sheet()
        remaining = 0
        for line in self.line_ids:
            if line.code == 'NET':
                remaining += line.total
        self.salary_remaining = remaining
        return res

    def salary_partial(self):
        if not self.contract_id.partial_credit_account_id or not self.contract_id.partial_debit_account_id:
            raise UserError(
                _('Make sure partial debit and credit accounts are selected in the Contract of ' + self.employee_id.name + '.'))
        else:
            return {
                'name': _('Partial Payment of ' + self.name),
                'type': 'ir.actions.act_window',
                'res_model': 'partial.payment',
                'view_mode': 'form',
                'target': 'new',
                'context': {
                    'default_payslip_id': self.id,
                }
            }


class HrPayslipRun(models.Model):
    _inherit = 'hr.payslip.run'

    # def payslip_done(self):
    #     if self.slip_ids:
    #         for slip in self.slip_ids:
    #             if slip.state != 'close':
    #                 slip.action_payslip_done()
    #     self.state = 'close'
