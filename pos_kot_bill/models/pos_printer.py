from odoo import api, fields, models, _
from odoo.exceptions import Warning

class PrintOrder(models.Model):
    _name = 'pos.printer'


    printer_name = fields.Char(string="KOT Printer")
    billing_printer = fields.Char(string='Receipt Printer')
    category_ids = fields.Many2many('pos.category', string="Category")
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.company.id)