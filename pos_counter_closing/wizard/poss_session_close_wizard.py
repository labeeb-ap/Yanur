# -*- coding: utf-8 -*-

from odoo import models, fields, _
from odoo.exceptions import ValidationError
from datetime import date
import requests

class PossSessionCloseWizard(models.TransientModel):
    _name = 'pos.session.close.wizard'
    _description = 'Pos Session Close Wizard'

    date = fields.Date(string="Close Date", help='Select closing date here', default=fields.Date.context_today)

    def session_close(self):
        session_ids = self.env['pos.session'].search([('state', '=', 'closed')])
        session_lst = []
        count = 0
        for session_id in session_ids:
            if session_id.stop_at.date() == self.date:
                session_lst.append(session_id.id)
                count += 1

        currency_type_ids = self.env['currency.type'].search([])
        cash_line_ids = []
        for currency_type_id in currency_type_ids:
            lines = (0, 0,
                     {'currency_type': currency_type_id.value}
                     )
            cash_line_ids.append(lines)
        payment_method_ids = self.env['pos.payment.method'].search([])
        other_payment_line_ids = []
        for payment_method_id in payment_method_ids:
            if (payment_method_id.is_cash_count and payment_method_id.is_credit) or \
                    (not payment_method_id.is_cash_count and not payment_method_id.is_credit):
                lines = (0, 0,
                         {'payment_method_id': payment_method_id.id
                          })
                other_payment_line_ids.append(lines)
        not_close_session_ids = self.env['pos.session'].search([('state', '!=', 'closed')])
        if not_close_session_ids:
            raise ValidationError(_("Please close all sub sessions."))
        if count == 0:
            raise ValidationError(_("There is no closed session with in this date."))

        # this part is for opening cash drawer
        cash_drawer_ids = self.env['cash.drawer.management'].search([])
        url = "http://{}/print/open-drawer".format(cash_drawer_ids.ip_addrs)
        payload = {'PrinterPath': cash_drawer_ids.printer_name, 'Copies': '1'}
        headers = {}

        response = requests.request("POST", url, headers=headers, data=payload)


        return {
            'name': _('Pos Session Close'),
            'type': 'ir.actions.act_window',
            'res_model': 'pos.session.close',
            'view_mode': 'form',
            'context': {
                'default_session_ids': [(6, 0, session_lst)],
                'default_date': self.date,
                'default_cash_line_ids': cash_line_ids,
                'default_payment_line_ids': other_payment_line_ids,

            },
        }
# class PossSessionCloseWizardStart(models.TransientModel):
#     _inherit= 'pos.details.wizard'
#
#     start_date = fields.Date(string="Start Date",required=True)
#     end_date = fields.Date(string="End Date",required=True)
