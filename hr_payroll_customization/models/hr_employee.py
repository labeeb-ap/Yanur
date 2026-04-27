from odoo import models, fields, api, _

class HrEmployee(models.Model):
    _inherit = "hr.employee"

    input_rule_line_ids = fields.One2many('employee.input.rule.line', 'employee_id', string="Input Rule Lines", copy=True)


class EmployeeInputRuleLine(models.Model):
    _name = 'employee.input.rule.line'

    employee_id = fields.Many2one('hr.employee', string='Employee')
    amount = fields.Float(string='Amount')
    rule_id = fields.Many2one('hr.salary.rule', string='Salary Rule', required=True)
    company_id = fields.Many2one(
        comodel_name='res.company',
        string='Company', required=True, readonly=True,
        default=lambda self: self.env.company)

