# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
import requests


class PosConfig(models.Model):
    _inherit = "pos.config"

    ip_address = fields.Char("IP Address")
    printer_name = fields.Char("Printer Name")
    is_sale_cash_drawer = fields.Boolean('Static IP')


    @api.model
    def cash_drawer_open(self, data):
        url = "http://{}/print/open-drawer".format(data['ip_address'])
        payload = {'PrinterPath': data['printer_name'], 'Copies': '1'}
        headers = {}

        response = requests.request("POST", url, headers=headers, data=payload)
        return {'result': 'success'}





class InvoiceConfig(models.Model):
    _name = "cash.drawer.management"
    _description = "Opening Cash Drawer"

    ip_addrs = fields.Char(string='IP Address')
    printer_name = fields.Char(string="Printer Name")
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.company.id)

class PosPaymentMethod(models.Model):
    _inherit = "pos.payment.method"

    is_reference = fields.Boolean(string='Add Reference')
