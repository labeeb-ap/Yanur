from odoo import models, fields, api, _
from odoo.exceptions import Warning


class EmployeeResignationDepartment(models.Model):
    _name = 'employee.resignation.department'
    _rec_name = 'name'

    name = fields.Char(string="Name")
    approved_user_id = fields.Many2one('res.users', string="Approve")

    @api.model
    def create(self, vals):
        res = super(EmployeeResignationDepartment, self).create(vals)
        blo = self.env['employee.resignation.department'].search([('name', '=', res.name)])
        if len(blo) > 1:
            raise Warning(_("Already Created The Department"))
        return res

    def write(self, vals):
        wr = super(EmployeeResignationDepartment, self).write(vals)
        wr_blo = self.env['employee.resignation.department'].search([('name', '=', self.name)])
        if len(wr_blo) > 1:
            raise Warning(_("Already Created The Department"))
        return wr


class HrEmployee(models.Model):
    _inherit = 'hr.employee'

    resignation_department_ids = fields.Many2many('employee.resignation.department', string="Department")
