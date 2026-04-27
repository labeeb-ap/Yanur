# -*- coding: utf-8 -*-
from odoo import models, fields, api, _


class HrPayslip(models.Model):
    _inherit = 'hr.payslip'

    additional_rule_amount = fields.Float(string='Additional Rule Amount', store=True)

    @api.onchange('date_from', 'employee_id')
    def _onchange_additional_input_rule(self):
        for rec in self:
            if rec.date_from and rec.employee_id:
                line_list = []
                input_ids = self.env['additional.input.rule.line'].search(
                    [('additional_input_rule_id.date', '>=', rec.date_from), ('employee_id', '=', rec.employee_id.id)])
                for input_id in input_ids:
                    line = (0, 0, {
                        'employee_id': input_id.employee_id.id,
                        'rule_id': input_id.additional_input_rule_id.rule_id.id,
                        'amount': input_id.amount
                    })
                    line_list.append(line)
                rec.employee_id.input_rule_line_ids = False
                rec.employee_id.write({'input_rule_line_ids': line_list})

    def compute_sheet(self):
        res =  super(HrPayslip, self).compute_sheet()

        for rec in self:
            rec._onchange_additional_input_rule()

        return res



