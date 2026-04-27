from odoo import api, fields, models, _
from datetime import date
from dateutil.relativedelta import relativedelta


class InheritEmployee(models.Model):
    _inherit = 'hr.employee'

    permanent_address = fields.Char(string='Permanant Address')
    temporary_address = fields.Char(string='Temporary Address')


class EmployeeIncentive(models.Model):
    _inherit = 'hr.contract'

    incentive = fields.Monetary(string="Incentive")

    def mail_reminder(self):
        hr = self.env['hr.employee'].sudo().search([('job_title', '=', 'HR')])
        match = self.env['hr.contract'].search([
            ('state', '=', 'open'),
            ('date_end', '=', fields.Date.today() + relativedelta(months=3))
        ])

        print(match)
        date_now = fields.Date.today()
        print(date_now)
        for i in match:
            mail_content = "  Hello  " + hr.name + ",<br>Document No: " + i.name + \
                           " is going to expire on " + \
                           str(i.date_end) + ". Please renew it before expiry date"
            main_content = {
                'subject': _('Document-%s Expired On %s') % (i.name, i.date_end),
                'author_id': self.env.user.partner_id.id,
                'body_html': mail_content,
                'email_to': hr.work_email,
            }
            self.env['mail.mail'].create(main_content).send()
            print("ccc")


