# -*- coding: utf-8 -*-
from odoo import fields, models, _, api


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    picking_type_id = fields.Many2one('stock.picking.type', 'Operation Type')
    box = fields.Float(string='Base Quantity in a Box', default=1)
    packing_per_carton = fields.Float(string='Packing Per Carton', default=1)
    type_in_carton = fields.Char(string='Carton Type')
    product_brand = fields.Char(string='Brand')
    # product_expiration = fields.Char(string='Shelf Life')
