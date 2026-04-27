# -*- coding: utf-8 -*-
from odoo import fields, models, api


class ResUsers(models.Model):
    _inherit = 'res.users'

    pos_user_type = fields.Selection([('cashier', 'Cashier'), ('salesman', 'Sales Person')], string="POS User Type",
                                     default='salesman')
    can_give_discount = fields.Boolean("Can Give Discount")
    can_change_price = fields.Boolean("Can Change Price")
    discount_limit = fields.Float("Discount Limit")
    based_on = fields.Selection([('pin', 'Pin'), ('barcode', 'Barcode')],
                                default='barcode', string="Authentication Based On")
    sales_persons = fields.Many2many('res.users', 'sales_person_rel', 'sales_person_id', 'user_id',
                                     string='Sales Person')
    custom_security_pin = fields.Char(string="Security Pin")

    @api.model
    def name_search(self, name, args=None, operator='ilike', limit=100):
        if self._context.get('from_sales_person'):
            users = []
            pos_users_ids = self.env.ref('point_of_sale.group_pos_user').users.ids
            sale_person_ids = self.search([('id', 'in', pos_users_ids),
                                           ('pos_user_type', '=', 'salesman')])
            selected_sales_persons = []
            for user in pos_users_ids:
                user_id = self.browse(user)
                if user_id.sales_persons:
                    selected_sales_persons.append(user_id.sales_persons.ids)
            if sale_person_ids:
                users.append(sale_person_ids.ids)
            if users:
                args += [['id', 'in', users[0]]]
            if selected_sales_persons:
                args += [['id', 'not in', selected_sales_persons[0]]]
        return super(ResUsers, self).name_search(name, args=args, operator=operator, limit=limit)

