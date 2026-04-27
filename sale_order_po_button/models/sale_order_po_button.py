from odoo import api, fields, models, _


class PurchaseOrder(models.Model):
    _inherit = 'sale.order'

    # purchase_items_count = fields.Integer(string='Rent', compute='_compute_purchase_items', store=True)
    is_true = fields.Boolean(string="Check",copy=False)

    # def _compute_purchase_items(self):
    #     for order in self:
    #         a = self.env['purchase.order.button'].search([('source_document', '=', order.id)])
    #         print("opppppppp", a)
    #         order.purchase_items_count = len(a)

    def action_create_purchase_order(self):
        print('approved', self.order_line)

        # print("bom",bom)
        # move_id = self.env['purchase.order'].sudo().create({
        #     'partner_id': 10,
        #     'date_order': self.exp_delivery_date
        # })
        bom_list = []
        item_list = []
        pro_id_list = []
        for line in self.order_line:

            bom = self.env['mrp.bom'].search([('product_tmpl_id', '=', line.product_id.product_tmpl_id.id)], limit=1,
                                             order='id desc')

            for line_id in bom.bom_line_ids:
                bom_dict = {}
                bom_dict['product_id'] = line_id.product_id.id
                bom_line_qty = line_id.product_qty / bom.product_qty
                production_qty = bom_line_qty * line.product_uom_qty
                bom_dict['product_qty'] = production_qty
                # if(bom_dict['product_id'] in tem_list):
                #     print("haii")
                # else:
                #     print("hhhhhh")
                item_list.append(bom_dict)
                pro_id_list.append({'data':
                                        {'pro': line_id.product_id.id}})

        print("tem", pro_id_list)
        list1 = []
        for list_id in pro_id_list:
            if list_id['data'] not in list1:
                list1.append(list_id['data'])
        print("list1", list1)
        list2 = []
        for a in list1:
            qty = 0
            pr = a['pro']
            for tem in item_list:
                if tem['product_id'] == pr:
                    qty += tem['product_qty']
            list2.append({
                'product_id': pr,
                'product_qty': qty
            })
        print(list2)
        #     if data['product_id']
        #     print(data,"=",data.values())
        #     any(data in list for list in tem_list)
        #     move_id.write({
        #         'order_line': [(0, 0, {
        #             'order_id': move_id.id,
        #             'product_id': line_id.product_id.id,
        #             'name': line_id.product_id.name,
        #             'product_qty': line_id.product_qty * line.quantity
        #         })]
        #     })
        # self._compute_purchase_items()
        action = {
            'name': 'Product',
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'purchase.order.button',
            'context': {
                # 'default_quote_id': self.quote_estimation_id.id,
                'default_event_date': self.exp_delivery_date,
                'default_order_line': list2,
                'default_source_document': self.id,
            },
            'target': 'new'
        }
        # self._compute_purchase_items()
        # print("kk", self.purchase_items_count)
        return action

    def create_purchase_order(self):
        # self._compute_purchase_items()
        return {
            'name': _('Purchase Order'),
            'type': 'ir.actions.act_window',
            'res_model': 'purchase.order',
            'view_mode': 'tree,form',
            'domain': [('source_document', '=', self.id)],
            # 'context': {'create': False,
            #             },
        }

    # def purchase_order_in_sale_order(self):
    #     res = super(PurchaseOrder).purchase_order_in_sale_order()
    #     self._compute_purchase_items()
    #     return res


class PurchaseOrderSo(models.Model):
    _inherit = 'purchase.order'

    source_document = fields.Many2one('sale.order', string='Source Document')
