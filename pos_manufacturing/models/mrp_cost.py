from odoo import models, fields, api


class MrpProduction(models.Model):
    _inherit = 'mrp.production'

    # component_product = fields.Many2one('product.product', 'Component Product', compute='_compute_component_product',
    #                                     store=True)
    # sales_price = fields.Float(string='Sales Price', compute='_compute_sales_price', store=True)

    # component_product = fields.Many2one('product.product', string='Component Product',
    #                                     compute='_compute_component_product', store=True)
    #
    # @api.depends('move_raw_ids.product_id')
    # def _compute_component_product(self):
    #     for production in self:
    #         component_products = production.move_raw_ids.mapped('product_id')
    #         print(component_products)
    #         if len(component_products) == 1:
    #             production.component_product = component_products
    #         else:
    #             production.component_product = False
    #
    # @api.depends('product_id', 'product_id.list_price')
    # def _compute_sales_price(self):
    #     for record in self:
    #         record.sales_price = record.product_id.list_price
