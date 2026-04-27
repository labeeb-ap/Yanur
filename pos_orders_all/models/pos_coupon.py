# -*- coding: utf-8 -*-
# Part of BrowseInfo. See LICENSE file for full copyright and licensing details.

from odoo import fields, models, api, _
from odoo.exceptions import AccessError, UserError, RedirectWarning, ValidationError, Warning
import random
from datetime import date, datetime
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT


class ProductTemp(models.Model):
    _inherit = 'product.template'

    is_coupon_product = fields.Boolean(string='Coupon Product')


class pos_gift_coupon(models.Model):
    _name = 'pos.gift.coupon'
    _description = "POS Gift Coupon"
    _order = "id desc"

    def print_report_coupons(self):
        return self.env.ref('pos_orders_all.action_gift_coupons').report_action(self)

    def existing_coupon(self, code):
        coupon_record = self.search([('c_barcode', '=', code)])
        if len(coupon_record) == 1:
            coupon_record = coupon_record[0]
            return True
        else:
            return False

    def pos_screen_search_coupon(self, code):
        coupon_record = self.search([('id', '=', code)])
        if coupon_record:
            return [coupon_record.id, coupon_record.name, coupon_record.expiry_date,
                    coupon_record.amount, coupon_record.issue_date, coupon_record.c_barcode,
                    coupon_record.amount_type, coupon_record.c_barcode_img
                    ]

    # def used_coupon(self):
    # 	self.is_sold == True
    # 	return True

    def search_coupon(self, code):
        coupon_record = self.search([('c_barcode', '=', code)])
        if coupon_record and coupon_record.product_id:
            if coupon_record.is_sold == False:
                coupon_record.is_sold = True
                sold_out = False
                return [coupon_record.id, coupon_record.amount, coupon_record.used,
                        coupon_record.coupon_count, coupon_record.coupon_apply_times,
                        coupon_record.expiry_date, coupon_record.partner_true,
                        coupon_record.partner_id.id, coupon_record.amount_type,
                        coupon_record.exp_dat_show, coupon_record.max_amount,
                        coupon_record.apply_coupon_on, coupon_record.product_id.id,
                        coupon_record.is_categ, coupon_record.categ_ids.ids, sold_out
                        ]
            else:
                sold_out = True
                return [coupon_record.id, coupon_record.amount, coupon_record.used,
                        coupon_record.coupon_count, coupon_record.coupon_apply_times,
                        coupon_record.expiry_date, coupon_record.partner_true,
                        coupon_record.partner_id.id, coupon_record.amount_type,
                        coupon_record.exp_dat_show, coupon_record.max_amount,
                        coupon_record.apply_coupon_on, coupon_record.product_id.id,
                        coupon_record.is_categ, coupon_record.categ_ids.ids, sold_out
                        ]
        else:
            return []

    @api.constrains('amount', 'exp_dat_show', 'issue_date', 'expiry_date', 'max_amount')
    def _check_config(self):

        # if self.amount_type == 'fix':
        # 	if self.max_amount and self.amount:
        # 		print("sarathmooooooooooooooooooooon",self.max_amount,self.amount)
        # 		if self.amount > self.max_amount:
        # 			raise Warning(_( "Coupon amount is greater than maximum amount"))

        if self.expiry_date and self.issue_date:
            if self.expiry_date < self.issue_date:
                raise Warning(_("Please Enter Valid Date.Expiry Date Should not be greater than Issue Date."))

    @api.model
    def search_user(self):
        res_partner = self.env['res.partner'].search([])
        user_list = []
        for i in res_partner:
            user_list.append(i.name)
        return user_list

    @api.model
    def create_coupon_from_ui(self, data):
        coup_obj = self.env['pos.gift.coupon']
        amt_type = False
        apply_coupon_on = data['apply_coupon_on']

        if data['c_am_type'] == 'Fixed':
            amt_type = 'fix'
        else:
            amt_type = 'per'

        if data['c_expdt_box']:
            exp_check_box = True
            expiry_checked = data['c_exp_dt']
        else:
            exp_check_box = False
            expiry_checked = False

        if data['c_cust_box']:
            cust_check_box = True
            customer_select = self.partner_id.search([('name', '=', data['c_customer'])]).id
        else:
            cust_check_box = False
            customer_select = False

        categ = []
        if data.get('coupon_categ'):
            for c in data.get('coupon_categ'):
                categ.append(int(c))

        vals = {
            'name': data['c_name'],
            'product_id': int(data['c_product']),
            'coupon_apply_times': data['c_limit'],
            'issue_date': data['c_issue_dt'],
            'amount': data['c_amount'],
            'amount_type': amt_type,
            'expiry_date': expiry_checked,
            'partner_id': customer_select,
            'exp_dat_show': exp_check_box,
            'partner_true': cust_check_box,
            'max_amount': data['coupon_max_amount'],
            'active': True,
            'apply_coupon_on': apply_coupon_on,
            'user_id': self.env.user.id,
        }
        if categ:
            vals.update({
                'is_categ': True,
                'categ_ids': [(6, 0, categ)]
            })

        res = coup_obj.sudo().create(vals)
        return [res.id, res.name, res.expiry_date, res.amount, res.issue_date,
                res.c_barcode, res.amount_type, res.c_barcode_img]

    @api.model
    def create(self, vals):
        last_coupon = self.search([], limit=1, order='id desc')
        vals['next_num'] = last_coupon.next_num + 1 if last_coupon else 1
        rec = super(pos_gift_coupon, self).create(vals)
        if rec.prefix:
            prefix = rec.prefix
            size = rec.seq_size
            # next_num = rec.next_num
            if rec.suffix:
                if rec.seq_size > 0:
                    base_code = prefix +rec.suffix + str(rec.next_num).zfill(size)
                else:
                    base_code = prefix + rec.suffix
                code = base_code
            else:
                if rec.seq_size > 0:
                    base_code = prefix + str(rec.next_num).zfill(size)
                else:
                    base_code = prefix
                code = base_code

        else:
            code = (random.randrange(1111111111111, 9999999999999))
        rec.write({'c_barcode': str(code)})
        # rec.next_num += 1
        return rec

    name = fields.Char('Name')
    product_id = fields.Many2one('product.product', string='Discount Product',
                                 domain="[('is_coupon_product', '=', True)]",
                                 help='The product used to model the discount.',
                                 default=lambda self: self.env['product.product'].search(
                                     [('is_coupon_product', '=', True)], limit=1).id)
    c_barcode = fields.Char(string="Coupon Barcode")
    c_barcode_img = fields.Binary('Coupon Barcode Image')
    user_id = fields.Many2one('res.users', 'Created By', default=lambda self: self.env.user)
    issue_date = fields.Datetime(default=datetime.now())
    exp_dat_show = fields.Boolean('Expiry Date.')
    expiry_date = fields.Datetime(string="Expiry Date")
    max_amount = fields.Float("Maximum amount")
    partner_true = fields.Boolean('Allow for Specific Customer')
    partner_id = fields.Many2one('res.partner')
    order_ids = fields.One2many('pos.order', 'coupon_id')
    active = fields.Boolean('Active', default=True)
    amount = fields.Float('Coupon Amount')
    amount_type = fields.Selection([('fix', 'Fixed'), ('per', 'percentage(%)')], default='fix', string="Amount Type")
    description = fields.Text('Note')
    used = fields.Boolean('Used')
    coupon_apply_times = fields.Integer('Coupon Code Apply Limit', default=1)
    coupon_count = fields.Integer('coupon count', default=1)
    coupon_desc = fields.Text('Description')
    apply_coupon_on = fields.Selection([('taxed', 'Taxed Amount'),
                                        ('untaxed', 'Untaxed Amount')], default='taxed', string="Apply Coupon on")
    is_categ = fields.Boolean('Allow for Specific Category')
    categ_ids = fields.Many2many('pos.category', string='POS Categories')
    is_sold = fields.Boolean('Sold')
    prefix = fields.Char(string="Prefix",default='GC')
    suffix = fields.Char(string="Suffix")
    seq_size = fields.Integer(string="Sequnce Size")
    next_num = fields.Integer(string="Next Number",default=1)

	# def _product_domain(self):


