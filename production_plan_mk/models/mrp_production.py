# -*- coding: utf-8 -*-
from odoo import fields, models, _, api
from odoo.exceptions import ValidationError, UserError


class MrpProduction(models.Model):
    _inherit = 'mrp.production'

    consignment = fields.Char(string='Consignment')
    plan_id = fields.Many2one('production.plan', string='Production Plan')
    plan_line_id = fields.Many2one('production.plan.line', string='Production Plan Line')
    picking_count = fields.Integer(string='Material Request', compute='_compute_material_request', store=True)
    box = fields.Float(string='Box')

    # project_id = fields.Many2one('project.project', string='Project')

    def _compute_material_request(self):
        for order in self:
            order.picking_count = self.env['stock.picking'].search_count([('mrp_production_id', '=', order.id)])

    def packing_material_request(self):
        # for lines in self.move_raw_ids:
        #     if not lines.picking_type_id:
        #         raise ValidationError(
        #             _("All Components should have Operation Type.",
        #               ))
        operation_type = self.move_raw_ids.mapped('product_id.product_tmpl_id.picking_type_id')
        # print('operation_type', operation_type.name)
        # print('operation_type', operation_type.tr)
        for op_type in operation_type:
            picking_ids = self.env['stock.picking'].search([('mrp_production_id', '=', self.id),
                                                            ('picking_type_id', '=', op_type.id)])
            if picking_ids:
                for picking_id in picking_ids:
                    picking_id.move_line_ids_without_package = False
                    self.env['stock.move'].search([('picking_id', '=', picking_id.id)]).unlink()
                    if picking_id.picking_type_id == op_type:
                        picking = picking_id
                    else:
                        picking = False
                    for line in self.move_raw_ids:
                        if line.product_id.product_tmpl_id.picking_type_id == op_type:
                            self.env['stock.move'].create({
                                'name': line.product_id.name,
                                'product_id': line.product_id.id,
                                'product_uom_qty': line.product_uom_qty,
                                'product_uom': line.product_uom.id,
                                'picking_id': picking.id,
                                'location_id': picking.location_id.id,
                                'location_dest_id': picking.location_dest_id.id,
                                # 'procure_method': 'make_to_order',
                                # 'origin': 'SOURCEDOCUMENT',
                                # 'state': 'draft',
                            })
            else:
                picking = self.env['stock.picking'].create({
                    'picking_type_id': op_type.id,
                    'mrp_production_id': self.id,
                    'location_id': op_type.default_location_src_id.id,
                    'location_dest_id': op_type.default_location_dest_id.id,
                    'origin': self.name,
                    'consignment': self.consignment,
                    # 'project_id': self.project_id.id,
                    # 'partner_id': self.env['ir.model.data'].xmlid_to_res_id('base.res_partner_4'),
                })
                for line in self.move_raw_ids:
                    if line.product_id.product_tmpl_id.picking_type_id == op_type:
                        self.env['stock.move'].create({
                            'name': line.product_id.name,
                            'product_id': line.product_id.id,
                            'product_uom_qty': line.product_uom_qty,
                            'product_uom': line.product_uom.id,
                            'picking_id': picking.id,
                            'location_id': picking.location_id.id,
                            'location_dest_id': picking.location_dest_id.id,
                            # 'procure_method': 'make_to_order',
                            # 'origin': 'SOURCEDOCUMENT',
                            # 'state': 'draft',
                        })

        self._compute_material_request()
        # picking.action_confirm()

    @api.onchange('box', 'product_id', 'product_qty')
    def _onchange_box(self):
        if self.product_id:
            if self.state == 'draft':
                if self.box != 0:
                    self.qty_producing = self.product_id.product_tmpl_id.box * self.box
                    self.product_qty = self.product_id.product_tmpl_id.box * self.box
                    # self._onchange_line_qty()
            else:
                if self.box != 0:
                    self.qty_producing = self.product_id.product_tmpl_id.box * self.box
                    # self.product_qty = self.product_id.product_tmpl_id.box * self.box

    @api.onchange('product_id', 'qty_producing', 'product_qty')
    def _onchange_product_uom_qty_box(self):
        if self.state != 'draft':
            if self.box != 0 and self.product_id.product_tmpl_id.box != 0:
                # (self.product_id.product_tmpl_id.box * self.box) or
                if self.qty_producing != self.product_id.product_tmpl_id.box * self.box:
                    raise UserError(_('The Box: %s and Quantity: %s of %s are not matching. please set box.', self.box,
                                      self.product_uom_qty, self.product_id.name))

    def created_internal_transfer_list(self):
        return {
            'name': _('Transfer'),
            'type': 'ir.actions.act_window',
            'res_model': 'stock.picking',
            'view_mode': 'tree,form',
            'domain': [('mrp_production_id', '=', self.id)],
            'context': {'create': False},
        }

    # @api.constrains('move_byproduct_ids')
    # def _constrains_move_by_products_ids(self):
    #     for se in self:
    #         if se.move_byproduct_ids:
    #             list1 = []
    #             list2 = []
    #             for pro in se.move_byproduct_ids:
    #                 list1.append(pro.product_id.id)
    #                 list2.append(pro.product_id.id)
    #             list3 = set(list2)
    #             if len(list1) != len(list3):
    #                 raise ValidationError(_('Product must be unique in By-Products'))
    #         else:
    #             raise ValidationError(_("By-Products are Empty"))


class StockMove(models.Model):
    _inherit = 'stock.move'

    on_hand = fields.Float(string="On Hand", related="product_tmpl_id.qty_available", store=True)


class StockMovePr(models.Model):
    _inherit = 'mrp.bom.line'

    purchase_uom_id = fields.Many2one('uom.uom', string="UOM",related="product_tmpl_id.uom_id")

#
#     picking_type_id = fields.Many2one(related='product_id.product_tmpl_id.picking_type_id', store=True)
