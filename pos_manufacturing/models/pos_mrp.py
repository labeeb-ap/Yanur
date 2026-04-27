from odoo import models, fields, api
from collections import defaultdict
from datetime import datetime, time
from odoo.exceptions import ValidationError


class PosOrder(models.Model):
    _inherit = 'pos.order'

    def create_manufacturing_order(self):
        today = datetime.now().date()
        start_of_today = datetime.combine(today, time.min)
        end_of_today = datetime.combine(today, time.max)

        orders = self.env['pos.order'].search([
            ('state', '=', 'paid'),
            ('date_order', '>=', start_of_today),
            ('date_order', '<=', end_of_today),
        ])

        for order in orders:
            # Check if a production order already exists for this POS order
            existing_production = self.env['mrp.production'].search([('pos_order_id', '=', order.id)], limit=1)
            if existing_production:
                continue

            product_qty_dict = defaultdict(float)

            for order_line in order.lines:
                product_qty_dict[order_line.product_id] += order_line.qty

            for product, qty in product_qty_dict.items():
                bom = product.product_tmpl_id.bom_ids[0] if product.product_tmpl_id.bom_ids else False
                # if not bom:
                #     continue

                if qty <= 0:
                    raise ValueError("Quantity to produce must be positive")

                production = self.env['mrp.production'].create({
                    'product_id': product.id,
                    'product_qty': qty,
                    'product_uom_id': product.uom_id.id,
                    'origin': order.name,
                    'bom_id': bom.id if bom else False,
                    'pos_order_id': order.id,
                })

                production._onchange_move_raw()
                production._onchange_producing()
                production._compute_state()
                production._compute_lines()
                production._onchange_move_finished()

        # self.is_true = True


class MrpProduction(models.Model):
    _inherit = 'mrp.production'

    pos_order_id = fields.Many2one('pos.order', string='Point of Sale Order')

    # component_product = fields.Many2one('product.product', string='Component Product',
    #                                     compute='_compute_component_product', store=True)

    sales_price = fields.Float(string='Sales Price', compute='_compute_sales_price', store=True)
    # bom_cost = fields.Float(string='BOM Cost', store=True)

    bom_cost = fields.Float(string='BOM Cost', compute='_compute_bom_cost', store=True)

    @api.depends('bom_id', 'product_qty')
    def _compute_bom_cost(self):
        for record in self:
            if record.product_qty:
                if record.product_qty > 0:
                    record.bom_cost = record.product_id.standard_price * record.product_qty

            # bom = record.bom_id
            # if bom and record.product_qty > 0:
            #     bom_cost = 0
            #     for bom_line in bom.bom_line_ids:
            #         component = bom_line.product_id
            #         component_qty = bom_line.product_qty
            #         component_cost = component.standard_price * component_qty
            #         bom_cost += component_cost
            #     record.bom_cost = bom_cost * record.product_qty
            # else:
            #     record.bom_cost = 0


    @api.depends('product_id', 'product_id.list_price','product_qty')
    def _compute_sales_price(self):
        for record in self:
            # record.sales_price = record.product_id.list_price
            if record.product_qty:
                if record.product_qty > 0:
                    record.sales_price = record.product_id.list_price * record.product_qty




    # @api.depends('move_raw_ids.product_id')
    # def _compute_component_product(self):
    #     for production in self:
    #         component_products = production.move_raw_ids.mapped('product_id')
    #         print(component_products)
    #         if len(component_products) == 1:
    #             production.component_product = component_products
    #         else:
    #             production.component_product = False

    def button_mark_done(self):
        res = super(MrpProduction, self).button_mark_done()
        context = self.env.context
        orders = self.env['mrp.production'].browse(context.get('active_ids'))
        print(orders)
        invalid_products = {}

        # Loop through each order and check the stock availability for each product
        for order in orders:
            invalid_products[order.name] = []
            for line in order.move_raw_ids:
                # Convert the product quantity to the UOM used in the order line
                qty = line.product_id.uom_id._compute_quantity(line.product_uom_qty, line.product_uom)

                # Get the product object
                product = line.product_id

                # Convert the quantity to the UOM used in the stock availability
                qty_available = product.uom_id._compute_quantity(product.qty_available, product.uom_id)

                if qty > qty_available:
                    # Only add products with negative quantity available
                    if qty_available < 0:
                        invalid_products[order.name].append(product.name)

        # Raise a validation error for all products that are not available in stock
        error_messages = []
        for order_name, product_names in invalid_products.items():
            if product_names:
                products_str = ",".join(product_names)
                error_messages.append(
                    "Insufficient stock for the following products in order %s: %s" % (order_name, products_str))

        if error_messages:
            error_message = "\n".join(error_messages)
            raise ValidationError(error_message)

        # context = self.env.context
        # orders = self.env['mrp.production'].browse(context.get('active_ids'))
        # invalid_products = []
        #
        # # Loop through each order and check the stock availability for each product
        # for order in orders:
        #     for line in order.move_raw_ids:
        #         # Convert the product quantity to the UOM used in the order line
        #         qty = line.product_id.uom_id._compute_quantity(line.product_uom_qty, line.product_uom)
        #
        #         # Get the product object
        #         product = line.product_id
        #
        #         # Convert the quantity to the UOM used in the stock availability
        #         qty_available = product.uom_id._compute_quantity(product.qty_available, product.uom_id)
        #
        #         if qty > qty_available:
        #             # Only add products with negative quantity available
        #             if qty_available < 0:
        #                 invalid_products.append(product.name)
        #
        # # Raise a validation error for all products that are not available in stock
        # if invalid_products:
        #     invalid_product_names = ", ".join(invalid_products)
        #     raise ValidationError('Insufficient stock for the following products: %s' % invalid_product_names)

        return res

        # Mark the production as done
        # production.button_mark_done()
        # # Add a message to the chatter
        # production.message_post(body='Production order marked as done.')
