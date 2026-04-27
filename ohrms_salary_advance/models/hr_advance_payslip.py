# -*- coding: utf-8 -*-
from datetime import datetime
from odoo import models


class SalaryRuleInput(models.Model):
    _inherit = 'hr.payslip'

    def get_inputs(self, contract_ids, date_from, date_to):
        """This Compute the other inputs to employee payslip.
                           """
        print('1111')
        res = super(SalaryRuleInput, self).get_inputs(contract_ids, date_from, date_to)
        contract_obj = self.env['hr.contract']
        emp_id = contract_obj.browse(contract_ids[0].id).employee_id
        adv_salary = self.env['salary.advance'].search([('employee_id', '=', emp_id.id)])
        amount = 0
        for adv_obj in adv_salary:
            current_date = date_from.month
            date = adv_obj.date
            existing_date = date.month
            if current_date == existing_date and adv_obj.state == 'approve':
                # state = adv_obj.state
                amount += adv_obj.advance
        print('amount...', amount)
        for result in res:
            if amount != 0 and result.get('code') == 'SAR':
                result['amount'] = amount
        return res