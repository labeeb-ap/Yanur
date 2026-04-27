# -*- coding: utf-8 -*-
from odoo import api, fields, models,_

#create a new class for MultipleProductSale. 
class MultipleProductSale(models.TransientModel):
    _name = "multiple.product.sale"
    _description = "Multiple Product Sale"
 
    product_ids = fields.Many2many('product.product',string='Products',domain=[('sale_ok','=',True)])

    def add_multiple_product_sale(self):
        order_line_object = self.env['sale.order.line']  
        if self.env.context.get('active_model')=='sale.order': 
            active_id = self.env.context.get('active_id',False)
            order_id = self.env['sale.order'].search([('id', '=', active_id)]) 
            if order_id and self.product_ids:    
                for record in self.product_ids:
                    if record:      
                        order_line_dict ={
                                  'order_id':order_id.id,
                                  'product_id':record.id,
                                  }          
                        order_line_object.create(order_line_dict)
            order_id.onchange_price_amount()

# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import models


class SaleAdvancePaymentInv(models.TransientModel):
    _inherit = "sale.advance.payment.inv"

    def _prepare_invoice_values(self, order, name, amount, so_line):
        res = super()._prepare_invoice_values(order, name, amount, so_line)
        res['price_amount'] = order.price_amount
        res['price_amount_min'] = order.price_amount_min
        res['pax_child_amount'] = order.pax_child_amount
        res['pax_child_qty'] = order.pax_child_amount
        return res

    # def _prepare_so_line(self, order, analytic_tag_ids, tax_ids, amount):
    #     res = super()._prepare_so_line(order, analytic_tag_ids, tax_ids, amount)
    #     if order.addi_true:
    #         res['is_rental_item'] = order.is_rental_item
    #     return res
