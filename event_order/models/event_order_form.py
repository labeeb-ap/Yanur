from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

HOURS_PER_DAY = 8


class SaleOrderCustomisation(models.Model):
    _inherit = 'sale.order'

    complimentory_food_new_id = fields.One2many(
        'complimentory.order.line',
        'order_id',
        string="Complimentory Foods"
    )
    complimentory_food_note = fields.Text(string="Complimentory Food Note")

    food_tasting_ids = fields.One2many(
        'food.tasting.details',
        'order_id',
        string="Food Tasting Details"
    )
    food_tasting_note = fields.Text(string="Food  Tasting Note")

    vip_food_details_ids = fields.One2many(
        'vip.food.details',
        'order_id',
        string="VIP Food Details"
    )
    vip_food_note = fields.Text(string="VIP Food Note")

    complimentory_food_id = fields.One2many('sale.order.line', 'complimentory_id')
    food_test_ids = fields.One2many('sale.order.line', 'food_id')
    vip_food_details = fields.One2many('sale.order.line', 'vip_food_id')

    date_order = fields.Date(string='Order Date', index=True, copy=False, default=fields.Datetime.now,
                             states={'sale': [('readonly', True)], 'done': [('readonly', True)]})
    ph_no = fields.Char(string="TEL / HP")
    fax = fields.Char(string="Fax")
    # time_site = fields.Float(string='Time Site')
    # time_yanur = fields.Float(string='Time Yanur')
    # event_time_format_1 = fields.Selection([('am', 'Am'), ('pm', 'Pm')], default="am")
    # event_time_format_2 = fields.Selection([('am', 'Am'), ('pm', 'Pm')], default="am")
    rental_item_ids = fields.One2many('rental.items', 'product_price_id', string="Rental Item", copy=True)
    venue = fields.Char(string='Venue')
    venue_com = fields.Char(string='Venue')
    food_venue = fields.Char(string='Venue')
    email_id = fields.Char(string="Email")
    events_date = fields.Date(string="Event Date")
    events_date_complementory = fields.Date(string="Date")
    events_date_food = fields.Date(string="Date")
    event_time_complementory = fields.Float(string="Time Site")
    event_time_ynr_complementory = fields.Float(string="Time Yanur")
    event_time_food = fields.Float(string="Time Site")
    event_time_food_format_1 = fields.Selection([('am', 'Am'), ('pm', 'Pm')], default="am")
    event_time_food_yanur = fields.Float(string="Time Yanur")
    event_time_food_yanur_format_1 = fields.Selection([('am', 'Am'), ('pm', 'Pm')], default="am")
    event_time_complementory_1 = fields.Selection([('am', 'Am'), ('pm', 'Pm')], default="am")
    event_time_ynr_complementory_1 = fields.Selection([('am', 'Am'), ('pm', 'Pm')], default="am")
    food_type = fields.Selection(
        [('breakfast', 'Breakfast'), ('lunch', 'Lunch'), ('dinner', 'Dinner'), ('hi_tea', 'Hi-Tea')], default='',
        string="Food Types")
    price_amount = fields.Float(string="Price Per Pax", default=0.0, copy=False)
    price_amount_min = fields.Integer(string="No Of Pax", default=0, copy=False)
    notes = fields.Text(string="Description")
    # pax = fields.Char(string="Pax")
    # event_title = fields.Selection([('private', 'Private'), ('corporate', 'Corporate'), ('government', 'Goverment')],default="",string="Event Title")
    # sales_man = fields.Many2one('res.partner', string="Sales Man", store=True)
    complementry_price_per_pax = fields.Float(string="Price Per Pax")
    food_price_per_pax = fields.Float(string="Price Per Pax")
    remarks_com = fields.Text(string="Remarks")
    remarks_food = fields.Text(string="Remarks")
    notes_notebook = fields.Text(string="Notes")
    nature_of_function = fields.Text(string="Nature Of Function")
    additional_amount = fields.Float(string="Additional amount", readonly=True, store=True,
                                     compute="compute_additional_amount")
    ic_number_customer = fields.Char(string="IC Number")

    breakfast_pax = fields.Integer("Breakfast Pax")
    breakfast_per_pax = fields.Float("Breakfast Per Pax")

    lunch_pax = fields.Integer("Lunch Pax")
    lunch_per_pax = fields.Float("Lunch Per Pax")

    dinner_pax = fields.Integer("Dinner Pax")
    dinner_per_pax = fields.Float("Dinner Per Pax")

    hi_tea_pax = fields.Integer("Hi Tea Pax")
    hi_tea_per_pax = fields.Float("Hi Tea Per Pax")

    
    total_pax_food = fields.Integer(string="Pax", default=0)
    total_pax_com = fields.Integer(string="Pax", default=0)
    price_per_pax = fields.Float(string="Price Per Pax")
    # event_food_company_wise = fields.Many2one('res.company')
    no_of_persons = fields.Integer(string="No Of Persons")
    total_amounts = fields.Float(string="Total", compute="_onchange_total_amounts")
    # total_amounts_payments = fields.Float(string="Total", compute="_compute_total_amounts_payments", store=True)
    discount_type = fields.Selection([('amount', 'Amount'), ('percentage', 'Percentage')], default="",
                                     string="Discount type")
    discount_amount = fields.Float(string="Discount")
    discount_line = fields.Float(string="Discount", readonly=True, copy=True)
    sub_total = fields.Float(string="Sub Total", readonly=True, compute="compute_sub_total", store=True)
    # part_timers = fields.One2many('part.timers', 'employee_id', string="Part Timers", copy=True)
    location_id = fields.Many2one('event.type.sale', string='Event Type', required=1)
    pax_child_amount = fields.Float(string="Price Per child Pax", default=0.0, copy=False)
    pax_child_qty = fields.Integer(string="No Of child Pax", default=0, copy=False)
    number_of_vip = fields.Integer(string="VIP", default=0)
    complementory_product_id = fields.Many2one('product.product', string="Product")

    # @api.depends('order_line.price_subtotal', 'additional_amount', 'discount_line')
    # def _amount_all(self):
    #
    #     res = super()._amount_all()
    #     for i in self:
    #         x = 0
    #         if i.sub_total or i.additional_amount or i.discount_line:
    #             subTotal = (i.price_amount * i.price_amount_min) + (i.pax_child_amount * i.pax_child_qty)
    #             x = subTotal - i.discount_line + i.additional_amount
    #             # x = i.sub_total + i.additional_amount
    #         i.amount_total = x
    #     return res

    # @api.onchange('location_id')
    # def _onchange_event_type_id(self):
    #     if not self.location_id:
    #         return
    #
    #     self.order_line = [
    #         (0, 0, {'product_id': p.id})
    #         for p in self.location_id.product_ids
    #     ]

    @api.depends('order_line.price_subtotal', 'additional_amount', 'discount_line')
    def _amount_all(self):
        res = super()._amount_all()
        for order in self:
            sub_total = (order.price_amount * order.price_amount_min) + (order.pax_child_amount * order.pax_child_qty)
            order.amount_total = sub_total - order.discount_line + order.additional_amount
        return res

    def copy_data(self, default=None):
        if default is None:
            default = {}

        if 'order_line' not in default:
            default['order_line'] = [(0, 0, line.copy_data()[0]) for line in
                                     self.order_line.filtered(lambda l: not l.addi_true)]

        default = super(SaleOrderCustomisation, self).copy_data(default=default)
        return default

    @api.onchange('price_amount', 'price_amount_min', 'order_line', 'pax_child_amount', 'pax_child_qty')
    def onchange_price_amount(self):
        if (self.price_amount > 0 and self.price_amount_min > 0 and self.order_line) or (
                self.pax_child_amount > 0 and self.pax_child_qty > 0 and self.order_line):
            result = (self.price_amount * self.price_amount_min) + (self.pax_child_amount * self.pax_child_qty)

            self.sub_total = result
            self.amount_total = self.sub_total
            order_line_count = len(self.order_line)

            each_subtotal = self.amount_total / order_line_count

            for line in self.order_line:
                if not line.addi_true:
                    each_unit_price = each_subtotal / line.product_uom_qty if line.product_uom_qty != 0 else 0
                    line.price_unit = each_unit_price


        else:
            if self.sub_total > 0:
                self.sub_total = 0

    @api.onchange('partner_id')
    def onchange_partner_id(self):
        res = super().onchange_partner_id()
        if self.partner_id:
            if self.partner_id.phone:
                self.ph_no = self.partner_id.phone
            if self.partner_id.ic_number:
                self.ic_number_customer = self.partner_id.ic_number
            if self.partner_id.email:
                self.email_id = self.partner_id.email
            else:
                self.ph_no = ""
                self.ic_number_customer = ""
                self.email_id = ""
        return res

    # @api.onchange( 'price_amount_min','order_line.price_subtotal')
    # def onchange_price_amount_min(self):
    #     print("yyyyy")
    #     if self.price_amount_min > 0 and self.price_amount > 0:
    #         print("roshna")
    # x = len(self.order_line)
    # amt = 0
    # if x > 0:
    #     amt = self.price_amount_min
    # for i in self.order_line:
    #     if i.product_id:
    #         i.product_uom_qty = amt
    #     else:
    #         i.product_uom_qty = 0

    def action_confirm(self):
        res = super(SaleOrderCustomisation, self).action_confirm()
        # self.onchange_price_amount()

        # for order in self:
        #     for i in self.picking_ids:
        #         print('iiii', i)
        #         for j in self.rental_item_ids:
        #             self.env['stock.move'].create({
        #                 'picking_id': i.id,
        #                 'product_id': j.rental_product.id,
        #                 'product_uom_qty': j.product_quantity,
        #                 'name': j.rental_product.name,
        #                 'product_uom': j.rental_product.uom_id.id,
        #                 'location_id': order.warehouse_id.lot_stock_id.id,
        #                 'location_dest_id': order.partner_shipping_id.property_stock_customer.id,
        #             })
        #         print('/////')

        # for rec in self.order_line:
        for k in self.rental_item_ids:
            self.env['sale.order.line'].create({
                'order_id': k.product_price_id.id,
                'product_id': k.rental_product.id,
                'product_uom_qty': k.product_quantity,
                'is_rental': True,
                'name': k.rental_product.name,
                'price_unit': k.product_price,
                'addi_true': True,
            })

        # self.onchange_price_amount()

        return res

    # @api.depends('rental_item_ids.product_sub_total')
    # def _compute_total_amounts(self):
    #     totall = 0
    #     for rec in self.rental_item_ids:
    #         if rec.product_sub_total:
    #             totall += rec.product_sub_total
    #     self.total_amounts = totall

    # (self.additional_amount = self.total_amounts) old commented

    @api.onchange('rental_item_ids.product_sub_total')
    def _onchange_total_amounts(self):
        totall = 0
        for rec in self.rental_item_ids:
            if rec.product_sub_total:
                totall += rec.product_sub_total
        self.total_amounts = totall

    # @api.depends('order_line.qty_delivered', 'order_line.addi_true')
    # def compute_additional_amount(self):
    #     addi_amount = 0
    #     u = 0
    #     for rec in self.order_line:
    #         if rec.price_subtotal and rec.addi_true == True:
    #             addi_amount += rec.price_subtotal
    #         self.additional_amount = addi_amount
    #         if rec.qty_delivered == 0:
    #             continue
    #         if rec.qty_delivered > 0 and rec.addi_true == True:
    #             rec.price_subtotal = rec.qty_delivered * rec.price_unit
    #             u += rec.price_subtotal
    #         self.additional_amount = u

    @api.depends('rental_item_ids.product_sub_total')
    def compute_additional_amount(self):
        for order in self:
            total_additional = sum(
                item.product_sub_total
                for item in order.rental_item_ids
                if item.product_sub_total
            )
            order.additional_amount = total_additional

    @api.depends('order_line.price_subtotal', 'order_line.addi_true', 'order_line.qty_delivered')
    def compute_sub_total(self):
        sub_totall = 0
        x = 0
        for rec in self.order_line:
            if rec.price_subtotal and rec.addi_true != True:
                sub_totall += rec.price_subtotal
            self.sub_total = sub_totall
            if rec.qty_delivered == 0:
                continue
            if rec.qty_delivered > 0 and rec.addi_true != True:
                x += rec.price_subtotal
            self.sub_total = x

    @api.onchange('discount_amount', 'discount_type')
    def onchange_discount_amount(self):
        if self.discount_amount:
            self.discount_line = self.discount_amount
            if self.discount_type == 'percentage':
                self.discount_line = (self.discount_amount * self.sub_total) / 100
            elif self.discount_type == 'amount':
                self.discount_line = self.discount_amount
            else:
                self.discount_line = 0

    @api.constrains('discount_line')
    def check_discount_line(self):
        for rec in self:
            if rec.sub_total < rec.discount_line:
                raise ValidationError(_(" discount amount cannot greater than the total ."))

    def _prepare_invoice(self):
        invoice_vals = super(SaleOrderCustomisation, self)._prepare_invoice()
        if self.additional_amount:
            invoice_vals['additional_amount'] = self.additional_amount
        if self.sub_total:
            invoice_vals['sub_total'] = self.sub_total
        if self.discount_line:
            invoice_vals['discount'] = self.discount_line
        if self.exp_delivery_date:
            invoice_vals['event_date'] = self.exp_delivery_date
        if self.price_amount_min:
            invoice_vals['pax_qty'] = self.price_amount_min
        if self.location_id.id:
            invoice_vals['event_id'] = self.location_id.id
        if self.complementry_price_per_pax:
            invoice_vals['compl_food_pric'] = self.complementry_price_per_pax
        if self.food_price_per_pax:
            invoice_vals['food_tast'] = self.food_price_per_pax
        invoice_vals['price_amount'] = self.price_amount
        invoice_vals['price_amount_min'] = self.price_amount_min
        invoice_vals['pax_child_amount'] = self.pax_child_amount
        invoice_vals['pax_child_qty'] = self.pax_child_amount
        return invoice_vals


class RentalItems(models.Model):
    _name = 'rental.items'

    rental_product = fields.Many2one('product.product', string="Product", required=True)
    product_quantity = fields.Float('Quantity', default=1, required=True)
    product_price = fields.Float(string="Price")
    description = fields.Char(string="Description")
    product_sub_total = fields.Float(string="Sub Total", compute="_compute_sub_total", store=True)
    product_price_id = fields.Many2one('sale.order')

    @api.onchange('rental_product')
    def onchange_product_price(self):
        if self.rental_product:
            self.product_price = self.rental_product.lst_price

    @api.depends('product_price', 'product_quantity')
    def _compute_sub_total(self):
        for rec in self:
            if rec.product_price and rec.product_quantity:
                rec.product_sub_total = rec.product_quantity * rec.product_price


# class PartTimers(models.Model):
#     _name = 'part.timers'
#
#     employee = fields.Many2one('res.partner', string="Employee", required=True)
#     working_hours = fields.Char(string='Working Hours', default=HOURS_PER_DAY, required=True)
#     payment = fields.Float(string='Payment', default=0.00, required=True)
#     employee_id = fields.Many2one('sale.order', string="employee")


class SaleOrderMoveLine(models.Model):
    _inherit = 'sale.order.line'

    pax = fields.Char(string="Pax")
    addi_true = fields.Boolean(string="Rental")
    complimentory_id = fields.Many2one('sale.order', string="order line", store=True)
    complimentory_food = fields.Many2one('product.product', string="Complimentory Food")
    complimentory_food_qty = fields.Integer(string="Quantity")
    total_pax_com = fields.Integer(string="Pax", default=0)
    complementry_price_per_pax = fields.Float(string="Price Per Pax")
    venue_com = fields.Char(string='Venue')
    events_date_complementory = fields.Date(string="Date")
    event_time_complementory = fields.Float(string="Time Site")
    event_time_ynr_complementory = fields.Float(string="Time Yanur")
    is_rental = fields.Boolean(string="Is Rental", defualt=False)

    # food taste section
    food_id = fields.Many2one('sale.order', string="food")
    food_taste_id = fields.Many2one('product.product', string="Tate Food")
    total_pax_food = fields.Integer(string="Pax", default=0)
    food_price_per_pax = fields.Float(string="Price Per Pax")
    food_venue = fields.Char(string='Venue')
    events_date_food = fields.Date(string="Date")
    event_time_food = fields.Float(string="Time Site")
    event_time_food_yanur = fields.Float(string="Time Yanur")

    # vip food details

    vip_food_id = fields.Many2one('sale.order', string="Food")
    vip_id = fields.Many2one('product.product', string="Food")

    @api.model
    def create(self, vals):
        # 1. Handle missing order_id
        if 'order_id' not in vals:
            if vals.get('complimentory_id'):
                vals['order_id'] = vals['complimentory_id']
            elif vals.get('food_id'):
                vals['order_id'] = vals['food_id']
            elif vals.get('vip_food_id'):
                vals['order_id'] = vals['vip_food_id']

        # 2. Determine Product ID from custom fields if missing
        if 'product_id' not in vals:
            if vals.get('complimentory_food'):
                vals['product_id'] = vals['complimentory_food']
            elif vals.get('food_taste_id'):
                vals['product_id'] = vals['food_taste_id']
            elif vals.get('vip_id'):
                vals['product_id'] = vals['vip_id']

        # 3. Handle missing name (Description)
        if 'name' not in vals:
            product_id = vals.get('product_id')
            if product_id:
                product = self.env['product.product'].browse(product_id)
                vals['name'] = product.get_product_multiline_description_sale()
            else:
                vals['name'] = "/"  # Fallback dummy value

        # 4. Handle missing UOM
        if 'product_uom' not in vals and vals.get('product_id'):
            product = self.env['product.product'].browse(vals['product_id'])
            vals['product_uom'] = product.uom_id.id if product.uom_id else False

        # 5. Handle missing Quantity
        if 'product_uom_qty' not in vals:
            if vals.get('complimentory_food_qty'):
                vals['product_uom_qty'] = vals['complimentory_food_qty']
            elif vals.get('total_pax_food'):  # Assuming pax maps to qty for food taste
                vals['product_uom_qty'] = vals['total_pax_food']
            else:
                vals['product_uom_qty'] = 1.0

        return super(SaleOrderMoveLine, self).create(vals)

    @api.onchange('product_id')
    def onchange_product_id(self):
        if self.order_id.price_amount == 0 or self.order_id.price_amount_min == 0:
            raise ValidationError('Please Enter The Pax')

    def _prepare_invoice_line(self, **optional_values):
        res = super()._prepare_invoice_line(**optional_values)
        res['is_rental_item'] = self.addi_true
        return res

    @api.onchange('product_id')
    def onchange_product_id(self):
        for line in self:
            if not line.order_id:
                return

            if line.order_id.price_amount == 0 or line.order_id.price_amount_min == 0:
                raise ValidationError('Please Enter The Pax')

            # ✅ SET QTY FROM PAX
            line.product_uom_qty = line.order_id.price_amount_min


class AdditionalRentalProducts(models.Model):
    _inherit = 'account.move'

    additional_amount = fields.Monetary(string="Rental Amount",
                                        readonly=True)  # compute="compute_additional_amount")
    sub_total = fields.Monetary(string="Sub Total", readonly=True)
    discount = fields.Monetary(string="Discount", readonly=True)
    event_date = fields.Date(string="Event Date")

    compl_food_pric = fields.Float(string='Complementory')
    food_tast = fields.Float(string='Food Taste')
    event_id = fields.Many2one('event.type.sale', string='Event Type', required=1)
    pax_child_amount = fields.Float(string="Price Per child Pax", default=0.0)
    pax_child_qty = fields.Integer(string="No Of child Pax", default=0)
    price_amount = fields.Float(string="Price Per Pax", default=0.0, copy=False)
    price_amount_min = fields.Integer(string="No Of Pax", default=0, copy=False)

    def action_post(self):
        res = super(AdditionalRentalProducts, self).action_post()
        if self.event_id.id:
            for line in self.line_ids:
                if line.analytic_account_id:
                    line.event_type_id = self.event_id.id

        return res

    @api.depends('sub_total', 'additional_amount', 'discount')
    def _compute_amount(self):
        res = super(AdditionalRentalProducts, self)._compute_amount()
        x = 0
        for i in self:
            if i.sub_total or i.additional_amount or i.discount:
                x = i.sub_total + i.additional_amount - i.discount
            if i.sub_total == 0:
                for j in i.invoice_line_ids:
                    x += j.price_subtotal
        self.amount_total = x

        return res


class LineidEvent(models.Model):
    _inherit = 'account.move.line'

    event_type_id = fields.Many2one('event.type.sale', string='Event Type', limit=1, copy=False)
    is_rental_item = fields.Boolean(string='Rental')


class ComplimentoryOrderLine(models.Model):
    _name = 'complimentory.order.line'
    _description = 'Complimentory Order Line'

    order_id = fields.Many2one(
        'sale.order',
        string="Sale Order",
        ondelete='cascade'
    )

    complimentory_food = fields.Many2one(
        'product.product',
        string="Complimentory Food"
    )

    complimentory_food_qty = fields.Float(
        string="Quantity"
    )

    total_pax_com = fields.Integer(
        string="Total Pax"
    )

    complementry_price_per_pax = fields.Float(
        string="Price Per Pax"
    )

    venue_com = fields.Char(
        string="Venue"
    )

    events_date_complementory = fields.Date(
        string="Event Date"
    )

    event_time_complementory = fields.Float(
        string="Event Time"
    )

    event_time_ynr_complementory = fields.Selection([
        ('am', 'AM'),
        ('pm', 'PM')
    ], string="Time Period")


class FoodTastingDetails(models.Model):
    _name = 'food.tasting.details'
    _description = 'Food Tasting Details'

    order_id = fields.Many2one(
        'sale.order',
        string="Sale Order",
        ondelete='cascade'
    )

    tasting_food_id = fields.Many2one(
        'product.product',
        string="Tasting Food"
    )

    tasting_qty = fields.Float(
        string="Quantity"
    )

    total_pax_tasting = fields.Integer(
        string="Total Pax"
    )

    price_per_pax_tasting = fields.Float(
        string="Price Per Pax"
    )

    venue_tasting = fields.Char(
        string="Venue"
    )

    tasting_date = fields.Date(
        string="Event Date"
    )

    tasting_time = fields.Float(
        string="Event Time"
    )

    tasting_time_period = fields.Selection([
        ('am', 'AM'),
        ('pm', 'PM')
    ], string="Time Period")

    remarks = fields.Text(
        string="Remarks"
    )


class VipFoodDetails(models.Model):
    _name = 'vip.food.details'
    _description = 'VIP Food Details'

    order_id = fields.Many2one(
        'sale.order',
        string="Sale Order",
        ondelete='cascade'
    )

    vip_id = fields.Many2one(
        'product.product',
        string="VIP Food"
    )
