from odoo import api, fields, models, _
from datetime import date
from odoo.exceptions import Warning


class KotCancelOrder(models.Model):
    _name = 'kot.canceled.order'
    _description = 'Canceled Kot'
    _rec_name = 'name'

    name = fields.Char(string='Name', default='New')
    date = fields.Date('Date', default=date.today())
    order_ref = fields.Char(string="Order reference")
    floor = fields.Char(string="Floor")
    table = fields.Char(string="Table")
    # product = fields.Many2one("product.template",string="Product")
    # quantity = fields.Float(string="Quantity")
    reason = fields.Char(string="Reason")
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.company.id)
    cancel_line_ids = fields.One2many('cancel.order.line', 'cancel_order_id', string='Line ids')

    @api.model
    def create(self, vals):
        vals['name'] = self.env['ir.sequence'].next_by_code('kot.canceled.orderline')
        return super(KotCancelOrder, self).create(vals)

    @api.model
    def canceled_order_lines(self, data,reason):
        print("canceled order",data)
        print("reason",reason)
        ref = data["name"]
        floor = data["floor"]
        table = data["table"]
        orderlines = data["lines"]
        # for i in lines:
        #     print(i["id"])
        #     print(i["name"])
        #     print(i["quantity"])
        # quantity = data[4]
        # cancel_reason = reason
        new_cancel_order = self.env['kot.canceled.order'].create({
            'order_ref': ref,
            'floor': floor,
            'table': table,
            'reason': reason,
        })
        for line in orderlines:
            new_cancel_order.sudo().write({
                'cancel_line_ids': [(0, 0, {
                    'cancel_order_id': new_cancel_order.id,
                    'product_id': int(line['id']),
                    'quantity': float(line['quantity'])
                })]
            })
        return True


class RentItemsLine(models.Model):
    _name = 'cancel.order.line'
    _description = 'Cancel Order Lines'

    cancel_order_id = fields.Many2one('kot.canceled.order', string='Canceled Order', store=True)
    product_id = fields.Many2one('product.product', string='Product', store=True)
    quantity = fields.Float(string='Quantity', store=True)