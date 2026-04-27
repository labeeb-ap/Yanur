# -*- coding: utf-8 -*-
from odoo import fields, models, _, api
from odoo.exceptions import UserError


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    # consignment = fields.Char(string='Consignment')
    # exp_delivery_date = fields.Date(string='Event Date')
    rent_items_count = fields.Integer(string='Rent', compute='_compute_rent_items', store=True)

    # @api.depends('state')
    def _compute_rent_items(self):
        for order in self:
            order.rent_items_count = self.env['rent.items'].search_count([('order_id', '=', order.id)])

    def action_create_rent_items(self):

        self._compute_rent_items()
        return {
            'name': _('Rent Items'),
            'type': 'ir.actions.act_window',
            'res_model': 'rent.items',
            'view_mode': 'form',
            'context': {
                'default_order_id': self.id,
                'default_exp_delivery_date': self.exp_delivery_date,
                # 'default_consignment': self.consignment,
                # 'default_project_id': self.project_id.id,
                # 'default_plan_line_ids': plan_line_ids,
            },
            'target': 'new',
        }


    def rent_items_list(self):
        return {
            'name': _('Rent Items'),
            'type': 'ir.actions.act_window',
            'res_model': 'rent.items',
            'view_mode': 'tree,form',
            'domain': [('order_id', '=', self.id)],
            'context': {'create': False},
        }

    def action_confirm(self):
        res = super(SaleOrder, self).action_confirm()
        self._compute_rent_items()
        return res