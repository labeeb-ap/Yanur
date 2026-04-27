from odoo import models, fields, api
#

class EventType(models.Model):
    _name = 'event.type.sale'
    _rec_name = 'event_type'

    event_type = fields.Char(string='Event Types')
    product_ids = fields.Many2many(
        'product.product',
        string="Products"
    )










