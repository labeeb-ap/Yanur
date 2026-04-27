from odoo import fields, models, api, _
from datetime import date
from odoo.exceptions import ValidationError


class ProductionPlan(models.Model):
    _name = 'production.plan'
    _description = 'Production Plan'
    _rec_name = 'name'

    name = fields.Char(string='Name', default='New')
    date = fields.Date('Date', default=date.today())
    order_id = fields.Many2one('sale.order', string='Sale Order')
    partner_id = fields.Many2one('res.partner', string='Customer')
    planning_date = fields.Date(string='Planning Date', default=date.today())
    exp_delivery_date = fields.Date(string='Event Date')
    plan_line_ids = fields.One2many('production.plan.line', 'plan_id', string='Line ids')
    consignment = fields.Char(string='Consignment')
    state = fields.Selection([('draft', 'Draft'), ('done', 'Done')], default='draft')
    # project_id = fields.Many2one('project.project', string='Project')



    @api.model
    def create(self, vals):
        if not vals.get('name') or vals['name'] == _('New'):
            vals['name'] = self.env['ir.sequence'].next_by_code('production.plan') or _('New')
        # self.env['sale.order'].browse(vals.get('order_id'))._compute_production_plan()
        a = self.env['sale.order'].browse(vals.get('order_id'))
        a._compute_production_plan()

        a.plan_count = 1
        if self.env['production.plan'].search_count([('order_id', '=', vals.get('order_id'))]) >= 1:
            raise ValidationError(_("You cannot create more than one production plan against a sale order."))
        # self.order_id.man = True
        return super(ProductionPlan, self).create(vals)

    def action_create_production_plan(self):
        # a = self.env['sale.order'].browse(vals.get('order_id'))
        # print("1",self.order_id.event_date)
        list1=[]
        for line in self.plan_line_ids:
            bom = self.env['mrp.bom'].search([('product_tmpl_id', '=', line.product_id.product_tmpl_id.id)], limit=1,
                                             order='id desc')
            if not bom:
                pass
                # raise ValidationError(_("All the Products should have proper BOM."))
            else:
                mrp = self.env['mrp.production'].create({
                    'product_id': line.product_id.id,
                    'product_uom_id': line.product_uom_id.id,
                    'box': line.box,
                    'product_qty': line.quantity,
                    'qty_producing': line.quantity,
                    'date_planned_start': self.order_id.exp_delivery_date,
                    'order_id':self.order_id.id,
                    'bom_id': bom.id,
                    'plan_id': self.id,
                    'origin': self.name,
                    # 'project_id': self.project_id.id,
                    'plan_line_id': line.id
                })
                mrp.update({
                    'location_src_id': mrp.picking_type_id.default_location_src_id.id,
                    'location_dest_id': mrp.picking_type_id.default_location_dest_id.id,
                })
                # print('picking', mrp.wer)
                mrp._onchange_move_raw()
                mrp._onchange_producing()
                mrp.action_confirm()
                mrp._compute_state()
                mrp._compute_lines()
                mrp._onchange_move_finished()
                mrp.state = 'confirmed'
                # if mrp.move_byproduct_ids:
                #     list1 = []
                #     list2 = []
                #     for pro in mrp.move_byproduct_ids:
                # print("haleeeeeeeeeeeeeeeeeeeeeee",line.quantity,bom.bom_line_ids)
                # for line_id in bom.bom_line_ids:
                #     dict1 = {}
                #     print(line_id.product_id.name,line_id.product_qty)
                #     quantity = line.quantity*line_id.product_qty
                #     dict1['product_name'] = line_id.product_id.name
                #     dict1['quantity'] = quantity
                #     list1.append(dict1)


            #         list1.append(pro.product_id.id)
            #         list2.append(pro.product_id.id)
            #     list3 = set(list2)
            #     if len(list1) != len(list3):
            #         raise ValidationError(_('Product must be unique in By-Products'))
            # else:
            #     raise ValidationError(_("By-Products are Empty"))
        self.order_id.man = True
        self.state = 'done'
        print("3", self.state)

    @api.onchange('order_id')
    def _onchange_order_id(self):
        self.partner_id = self.order_id.partner_id.id,
        if self.order_id.consignment:
            self.consignment = self.order_id.consignment
        else:
            self.consignment = False
        if self.order_id.exp_delivery_date:
            self.exp_delivery_date = self.order_id.exp_delivery_date
        else:
            self.exp_delivery_date = False
        self.plan_line_ids = False
        for line in self.order_id.order_line:
            self.write({'plan_line_ids': [(0, 0, {'product_id': line.product_id.id,
                                                  'box': line.box,
                                                  'quantity': line.product_uom_qty,
                                                  'product_uom_id': line.product_uom.id, })]})


class ProductionPlanLine(models.Model):
    _name = 'production.plan.line'
    _description = 'Production Plan Lines'

    plan_id = fields.Many2one('production.plan', string='Production Plan', store=True)
    product_id = fields.Many2one('product.product', string='Product', store=True)
    box = fields.Float(string='Box', store=True)
    quantity = fields.Float(string='Quantity', store=True)
    product_uom_id = fields.Many2one('uom.uom', string='Unit', store=True)
    exp_production_date = fields.Date(string='Expected Production Date', default=date.today(), store=True)

class ManufacturingSaleOrder(models.Model):
    _inherit = 'sale.order'
    _description = 'Production Plan Lines'

    man = fields.Boolean(string="Manafacturing",copy=False)


    def manufacturing_list(self):
        return{
            'name': _('Manfacturing Orders'),
            'type': 'ir.actions.act_window',
            'res_model': 'mrp.production',
            'view_mode': 'tree,form',
            'domain': [('order_id', '=', self.id)],
            'context': {'create': False},
        }

class ManufacturingField(models.Model):
    _inherit = 'mrp.production'

    order_id = fields.Many2one('sale.order',string="Order")