from odoo import models, fields, api, _


class SaleorderPO(models.TransientModel):
    _name = "purchase.order.button"
    _description = "sale order po"

    vendor_name = fields.Many2one('res.partner', string='Vendor')
    order_date = fields.Date(string='Order Date')
    event_date = fields.Date(string='Event Date', required=True)
    source_document = fields.Many2one('sale.order', string='Source Document')
    order_line = fields.One2many('order.line', 'source_id', string="Order Line")

    def purchase_order_in_sale_order(self):
        x = self.env['purchase.order'].create({
            'partner_id': self.vendor_name.id, 'date_order': self.event_date, 'source_document': self.source_document.id})
        for i in self.order_line:
            # self.env['purchase.order.line'].create({
            self.write({'order_line': [(0, 0, {
                # 'order_id': x.id,
                'product_id': i.product_id.id,
                # 'name': i.product_id,
                'product_qty': i.product_qty,
                # 'date_planned': self.event_date,
            })]})
        # self.source_document.purchase_items_count += 1
        self.source_document.is_true = True
        # self._compute_purchase_items()


class OrderLine(models.TransientModel):
    _name = 'order.line'
    _description = "order line"

    product_id = fields.Many2one('product.product', string='Product')
    product_qty = fields.Float(string='Quantity')
    source_id = fields.Many2one('purchase.order.button', string='Source')
