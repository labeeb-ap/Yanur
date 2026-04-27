from odoo import models, fields, api, _

class AdditionalInputRule(models.Model):
    _name = 'additional.input.rule'
    _inherit = 'mail.thread'
    _rec_name = 'rule_id'

    rule_id = fields.Many2one('hr.salary.rule', string='Salary Rule', required=True, tracking=True)
    date = fields.Date(string="validity", store=True, required=True, tracking=True)
    input_rule_line_ids = fields.One2many('additional.input.rule.line', 'additional_input_rule_id', string="Input Rule Lines", copy=True)
    company_id = fields.Many2one(
        comodel_name='res.company',
        string='Company', required=True, readonly=True,
        default=lambda self: self.env.company)
    _sql_constraints = [
        ('unique_rule_id', 'unique(rule_id)', 'The Salary Rule should not use more than once!'),
    ]
    ### NEW TO GENERATE ALL EMPLOYEES
    def generate_employee_lines(self):
        """ Generate input rule lines for all employees in the company """
        for record in self:
            employees = self.env['hr.employee'].search([('company_id', '=', record.company_id.id)])

            # Remove existing lines to avoid duplicates
            record.input_rule_line_ids.unlink()

            # Create new lines for all employees
            lines = [(0, 0, {
                'employee_id': emp.id,
                'barcode': emp.barcode,  # Fetching employee's barcode
                'amount': 0.0,  # Default amount (modifiable)
                'company_id': record.company_id.id
            }) for emp in employees]

            record.write({'input_rule_line_ids': lines})


class AdditionalInputRuleLine(models.Model):
    _name = 'additional.input.rule.line'

    additional_input_rule_id = fields.Many2one('additional.input.rule', string='Additional Input')
    employee_id = fields.Many2one('hr.employee', string='Employee', required=True)
    barcode = fields.Char(related='employee_id.barcode',string='Badge ID')
    amount = fields.Float(string='Amount')
    company_id = fields.Many2one(
        comodel_name='res.company',
        string='Company', required=True, readonly=True,
        default=lambda self: self.env.company)

