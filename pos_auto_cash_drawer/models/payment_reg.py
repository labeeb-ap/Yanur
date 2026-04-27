# See LICENSE file for full copyright and licensing details.

from odoo import fields, models
import requests

class RegisterPayment(models.TransientModel):
    _inherit = "account.payment.register"

    def action_create_payments(self):
        res = super().action_create_payments()
        if self.journal_id.type == 'cash':
            cash_drawer_ids = self.env['cash.drawer.management'].search([])
            url = "http://{}/print/open-drawer".format(cash_drawer_ids.ip_addrs)
            payload = {'PrinterPath': cash_drawer_ids.printer_name, 'Copies': '1'}
            headers = {}

            response = requests.request("POST", url, headers=headers, data=payload)
        return res


