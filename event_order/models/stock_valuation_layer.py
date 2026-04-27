from odoo import models, fields,api
#

class Stock(models.Model):
    _inherit = 'stock.valuation.layer'

    value = fields.Float(string='Total Value',store=True)










