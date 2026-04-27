# -*- coding: utf-8 -*-
from odoo import fields, models, _, api
from odoo.exceptions import UserError


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    consignment = fields.Char(string='Consignment')
    exp_delivery_date = fields.Date(string='Event Date')
    plan_count = fields.Integer(string='Planning', compute='_compute_production_plan', store=True)
    time_site = fields.Float(string='Time Site')
    time_yanur = fields.Float(string='Time Yanur')
    event_time_format_1 = fields.Selection([('am', 'Am'), ('pm', 'Pm')], default="am")
    event_time_format_2 = fields.Selection([('am', 'Am'), ('pm', 'Pm')], default="am")
    event_title = fields.Selection([('private', 'Private'), ('corporate', 'Corporate'), ('government', 'Goverment')],
                                   default="", string="Event Title")
    sales_man = fields.Many2one('res.partner', string="Sales Man", store=True)

    # def _prepare_invoice(self):
    #     invoice_vals = super(SaleOrder, self)._prepare_invoice()
    #     if self.exp_delivery_date:
    #         invoice_vals['event_date'] = self.exp_delivery_date

    @api.depends('state')
    def _compute_production_plan(self):
        for order in self:
            order.plan_count = self.env['production.plan'].search_count([('order_id', '=', order.id)])

    def action_create_production_plan(self):
        print("s1", self.state)
        plan_line_ids = []
        for line in self.order_line:
            lines = (0, 0, {
                'product_id': line.product_id.id,
                'box': line.box,
                'quantity': line.product_uom_qty,
                # 'exp_production_date': self.date,
                'product_uom_id': line.product_uom.id,
            })
            plan_line_ids.append(lines)
        # move_dict['line_ids'] = line_ids
        self._compute_production_plan()
        print("s2", self.state)
        return {
            'name': _('Production Plan'),
            'type': 'ir.actions.act_window',
            'res_model': 'production.plan',
            'view_mode': 'form',
            'context': {
                'default_order_id': self.id,
                'default_partner_id': self.partner_id.id,
                'default_exp_delivery_date': self.exp_delivery_date,
                'default_consignment': self.consignment,
                # 'default_project_id': self.project_id.id,
                'default_plan_line_ids': plan_line_ids,
            },
            'target': 'new',
        }

    def planned_list(self):
        return {
            'name': _('Production Plan'),
            'type': 'ir.actions.act_window',
            'res_model': 'production.plan',
            'view_mode': 'tree,form',
            'domain': [('order_id', '=', self.id)],
            'context': {'create': False},
        }
        # plan_line_ids = []
        # for line in self.order_line:
        #     lines = (0, 0, {
        #         'product_id': line.product_id.id,
        #         'quantity': line.product_uom_qty,
        #         # 'exp_production_date': self.date,
        #         'product_uom_id': line.product_uom.id,
        #     })
        #     plan_line_ids.append(lines)
        # # move_dict['line_ids'] = line_ids
        # print('plan_line_ids', plan_line_ids)
        # return {
        #     'name': _('Production Plan'),
        #     'type': 'ir.actions.act_window',
        #     'res_model': 'production.plan',
        #     'view_mode': 'tree,form',
        #     'domain': [('order_id', '=', self.id)],
        #     'context': {
        #         'context': {'create': False},
        #         # 'default_order_id': self.id,
        #         # 'default_partner_id': self.partner_id.id,
        #         # 'default_exp_delivery_date': self.exp_delivery_date,
        #         # 'default_consignment': self.consignment,
        #         # 'default_plan_line_ids': plan_line_ids,
        #     },
        #     # 'target': 'new',
        # }

    def action_confirm(self):
        res = super(SaleOrder, self).action_confirm()
        print('res', res)
        self._compute_production_plan()
        return res


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    box = fields.Float(string='Box')
    box_count = fields.Float(string='Box Count')
    product_expiration = fields.Char(string='Shelf Life', default='18 Months')

    # @api.onchange('product_id')
    # def _onchange_box_count(self):
    #     if self.product_id:
    #         self.box_count = self.product_id.product_tmpl_id.box

    @api.onchange('product_id', 'box')
    def _onchange_box_qty(self):
        if self.product_id:
            self.box_count = self.product_id.product_tmpl_id.box
            if self.box != 0:
                self.product_uom_qty = self.product_id.product_tmpl_id.box * self.box
                self.box_count = self.product_id.product_tmpl_id.box

    @api.onchange('product_id', 'product_uom_qty')
    def _onchange_product_uom_qty_box(self):
        if self.box != 0 and self.product_id.product_tmpl_id.box != 0:
            if self.product_uom_qty != self.product_id.product_tmpl_id.box * self.box:
                raise UserError(_('The Box: %s and Quantity: %s of %s are not matching. please set box.', self.box,
                                  self.product_uom_qty, self.name))

    def _prepare_invoice_line(self, **optional_values):
        res = super(SaleOrderLine, self)._prepare_invoice_line(**optional_values)
        res.update({
            'box': self.box,
            'box_count': self.box_count,
            'product_expiration': self.product_expiration,
        })
        return res
