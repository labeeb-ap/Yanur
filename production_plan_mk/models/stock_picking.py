# -*- coding: utf-8 -*-
from odoo import fields, models


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    mrp_production_id = fields.Many2one('mrp.production', string='MRP')
    consignment = fields.Char(string='Consignment')
    # project_id = fields.Many2one('project.project', string='Project')
