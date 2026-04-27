# -*- coding: utf-8 -*-
from odoo import fields, models, _, api


class StockPickingType(models.Model):
    _inherit = 'stock.picking.type'

    # user_ids = fields.Many2many('res.users', 'stock_picking_type_rel', string='Allowed Users', store=True)
    user_ids = fields.Many2many('res.users', string='Allowed Users', store=True)

