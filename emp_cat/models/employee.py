from odoo import fields, api, models, _
from calendar import monthrange
from odoo.exceptions import ValidationError


class EmployCategorize(models.Model):
    _inherit = 'hr.employee'

    period_type = fields.Selection([('prob', 'Probation'), ('perm', 'Permanent'), ('cont', 'Contract')], default="perm")
    max_sick_leave_probation = fields.Integer(string="Max Sick Leave Probation")
    max_casual_leave_probation = fields.Integer(string="Max Casual Leave Probation")
    max_casual_leave_permanent = fields.Integer(string="Max Casual Leave Permanent")
    max_sick_leave_permanent = fields.Integer(string="Max Sick Leave Permanent")
    max_sick_leave_contract = fields.Integer(string="Max Sick Leave contract")
    max_casual_leave_contract = fields.Integer(string="Max Casual Leave contract")
    expiry_date = fields.Date(string="Expiry Date")
    pf_num = fields.Char(string='PF Number')
    esi_num = fields.Char(string='ESI Number')
    gmc_num = fields.Char(string='GMC Number')
    employee_code = fields.Char(string='Employee Code', copy=False)
    joining_date = fields.Date(string='Date of Joining')
    job_type = fields.Selection([('on_roll', 'On-Roll'), ('contract_labour', 'Contract Labour')], string='Job Type')

    @api.model
    def create(self, vals):
        res = super(EmployCategorize, self).create(vals)
        if res.employee_code:
            blo = self.env['hr.employee'].search(
                [('employee_code', '=', res.employee_code)])
            if len(blo) > 1:
                raise ValidationError(_("Employee Code Must Be Unique !"))
        return res

    def write(self, vals):
        wr = super(EmployCategorize, self).write(vals)
        wr_blo = self.env['hr.employee'].search(
            [('employee_code', '=', self.employee_code)])
        if len(wr_blo) > 1:
            raise ValidationError(_("Employee Code Must Be Unique !"))
        return wr

    # @api.model
    # def create(self, vals):
    #     # if vals.get('active') == False:
    #     if vals.get('employee_code') == False:
    #         if vals['job_type'] == 'on_roll':
    #             vals['employee_code'] = self.env['ir.sequence'].next_by_code('hr.employee.on.roll') or 'New'
    #         if vals['job_type'] == 'contract_labour':
    #             vals['employee_code'] = self.env['ir.sequence'].next_by_code('hr.employee.contract.labour') or 'New'
    #     result = super(EmployCategorize, self).create(vals)
    #     return result

    def get_unpaid_payslip(self, employee_id, from_date, to_date, payslip):
        date_diff = to_date - from_date
        # month_days = date_diff.days + 1
        month_days = monthrange(from_date.year, from_date.month)[1]
        one_day_salary = payslip.contract_id.wage / month_days
        emp_tot_unpaid_leave_count = 0.0
        unpaid_leave = self.env.ref('hr_holidays.holiday_status_unpaid')
        # print('fun para', self, employee_id, from_date, to_date, payslip)
        if employee_id and from_date and to_date:
            total_emp_leaves = self.env['hr.leave'].search(
                [('state', '=', 'validate'),
                 ('holiday_status_id.name', '=', unpaid_leave.name)])
            for tot_leave in total_emp_leaves:
                if tot_leave.request_date_from.year == from_date.year and \
                        tot_leave.request_date_from.month == from_date.month and \
                        tot_leave.employee_id.id == employee_id:
                    emp_tot_unpaid_leave_count += tot_leave.number_of_days
            return emp_tot_unpaid_leave_count * one_day_salary

    def get_unpaid_payslips(self, employee_id, from_date, to_date, payslip):
        date_diff = to_date - from_date
        month_days = date_diff.days + 1
        one_day_salary = payslip.contract_id.wage / month_days
        emp_tot_unpaid_leave_count = 0.0
        unpaid_leave = self.env.ref('hr_holidays.holiday_status_unpaid')
        print('uplv', unpaid_leave)
        print('fun para', self, employee_id, from_date, to_date, payslip)
        if employee_id and from_date and to_date:
            total_emp_leaves = self.env['hr.leave'].search(
                [('employee_id', '=', employee_id), ('state', '=', 'validate'),
                 ('holiday_status_id.name', '=', unpaid_leave.name),
                 ('request_date_from.year', '=', from_date.year),
                 ('request_date_from.month', '=', from_date.month)])
            days = 0
            for tot_leave in total_emp_leaves:
                days += tot_leave.number_of_days
                print(tot_leave.holiday_status_id.name, unpaid_leave.name)
                if tot_leave.holiday_status_id.name == unpaid_leave.name:
                    if tot_leave.request_unit_half:
                        emp_tot_unpaid_leave_count += 0.5
                    elif tot_leave.number_of_days:
                        emp_tot_unpaid_leave_count += tot_leave.number_of_days
            print('days', days)
            return emp_tot_unpaid_leave_count * one_day_salary

    @api.onchange('period_type')
    def _onchange_period_type(self):
        for rec in self:
            if rec.period_type == 'prob':
                rec.max_sick_leave_permanent = 0
                rec.max_casual_leave_permanent = 0
                rec.max_sick_leave_probation = 6
                rec.max_casual_leave_probation = 12
            elif rec.period_type == 'perm':
                rec.max_sick_leave_probation = 0
                rec.max_casual_leave_probation = 0
                rec.max_sick_leave_permanent = 6
                rec.max_casual_leave_permanent = 18

    def get_leave_payslip(self, employee_id, from_date, to_date, payslip):
        date_diff = to_date - from_date
        month_days = date_diff.days + 1
        one_day_salary = payslip.contract_id.wage / month_days
        emp_tot_casual_leave_count = emp_tot_sick_leave_count = 0.0
        total_casual_exclude_current_month = total_sick_exclude_current_month = 0
        add_leave_days = 0
        casual_leave_count = sick_leave_count = 0.0
        if employee_id and from_date and to_date:
            total_emp_leaves = self.env['hr.leave'].search(
                [('employee_id', '=', employee_id), ('state', '=', 'validate')])
            for tot_leave in total_emp_leaves:
                if tot_leave.type_of_leave == 'casual':
                    if tot_leave.request_unit_half:
                        emp_tot_casual_leave_count += 0.5
                    elif tot_leave.number_of_days:
                        emp_tot_casual_leave_count += tot_leave.number_of_days
                else:
                    if tot_leave.request_unit_half:
                        emp_tot_sick_leave_count += 0.5
                    elif tot_leave.number_of_days:
                        emp_tot_sick_leave_count += tot_leave.number_of_days
            leaves = self.env['hr.leave'].search(
                [('employee_id', '=', employee_id), ('date_from', '>=', from_date), ('date_to', '<=', to_date),
                 ('state', '=', 'validate')])

            for leave in leaves:
                if leave.type_of_leave == 'casual':
                    if leave.request_unit_half:
                        casual_leave_count += 0.5
                    elif leave.number_of_days:
                        casual_leave_count += leave.number_of_days

                else:
                    if leave.request_unit_half:
                        sick_leave_count += 0.5
                    elif leave.number_of_days:
                        sick_leave_count += leave.number_of_days

            total_casual_exclude_current_month = emp_tot_casual_leave_count - casual_leave_count
            total_sick_exclude_current_month = emp_tot_sick_leave_count - sick_leave_count

            employee_record = self.env['hr.employee'].browse(employee_id)

            if employee_record.period_type == 'perm':
                if total_casual_exclude_current_month <= employee_record.max_casual_leave_permanent:
                    if casual_leave_count > 2:
                        add_leave_days = casual_leave_count - 2
                else:
                    add_leave_days = casual_leave_count
                if total_sick_exclude_current_month > employee_record.max_sick_leave_permanent:
                    if sick_leave_count:
                        add_leave_days += sick_leave_count
                else:
                    if sick_leave_count > employee_record.max_sick_leave_permanent:
                        add_sick_leave_count = sick_leave_count - employee_record.max_sick_leave_permanent
                        add_leave_days += add_sick_leave_count

                return add_leave_days * one_day_salary

            elif employee_record.period_type == 'prob':
                if total_casual_exclude_current_month <= employee_record.max_casual_leave_probation:
                    if casual_leave_count > 1:
                        add_leave_days = casual_leave_count - 1
                else:
                    add_leave_days = casual_leave_count

                if total_sick_exclude_current_month > employee_record.max_sick_leave_probation:
                    if sick_leave_count:
                        add_leave_days += sick_leave_count
                else:
                    if sick_leave_count > employee_record.max_sick_leave_probation:
                        add_sick_leave_count = sick_leave_count - employee_record.max_sick_leave_probation
                        add_leave_days += add_sick_leave_count

                return add_leave_days * one_day_salary

        return 0
