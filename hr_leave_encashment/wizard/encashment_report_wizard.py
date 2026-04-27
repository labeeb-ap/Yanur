from odoo import models, fields


class EncashmentReportWizard(models.TransientModel):
    _name = 'encashment.report.wizard'
    _description = 'Encashment Report Wizard'

    from_date = fields.Date(string='From Date')
    to_date = fields.Date(string='To Date')
    employee_id = fields.Many2one('hr.employee', string='Employee')

    def print_encashment_report(self):
        print('//')

