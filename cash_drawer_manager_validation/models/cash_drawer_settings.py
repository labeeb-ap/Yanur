from odoo import models, fields, api
import requests


class CashDrawerSettings(models.Model):
    _name = 'cash.drawer.settings'
    _description = 'Cash Drawer Settings'
    _rec_name = 'name'

    name = fields.Char(string='Name', default='New')
    employee = fields.Many2one("hr.employee",string='Employee')
    drawer_pin = fields.Char("Cash Drawer Pin")
    company_id = fields.Many2one('res.company', string='Company', required=True, default=lambda self: self.env.company)

    @api.model
    def create(self, vals):
        vals['name'] = self.env['ir.sequence'].next_by_code('cash.drawer.settings')
        return super(CashDrawerSettings, self).create(vals)

#     @api.model
#     def open_cash_drawer(self, data):
#         result = 'fail'
#         emp_ids = self.env['hr.employee'].search([
#                 ('emp_position', '=', "manager")
#             ])
#         print(emp_ids)
#         if emp_ids:
#             for emp in emp_ids:
#                 print(emp.name)
#                 if emp.drawer_pin == data['pin']:
#                     result = 'success'
#                     url = "http://{}/print/open-drawer".format(data['ip_address'])
#                     payload = {'PrinterPath': data['printer_name'], 'Copies': '1'}
#                     headers = {}
#                     # response = requests.request("POST", url, headers=headers, data=payload)
#                     return {'result': result}
#                 else:
#                     return {'result': result}
#         else:
#             return {'result': result}
#
#
# class HrManagerPublic(models.Model):
#     _inherit = 'hr.employee.public'
#
#     emp_position = fields.Selection([('staff', 'Staff'), ('manager', 'Manager')],default='staff',
#                                      string='Position')
#     drawer_pin = fields.Char("Cash Drawer Pin")