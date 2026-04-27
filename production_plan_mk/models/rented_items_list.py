from odoo import fields, models, api, _
from datetime import date
from odoo.exceptions import ValidationError
import base64
from odoo.http import request
from odoo.tools import date_utils
from odoo.tools.safe_eval import json


class RentItems(models.Model):
    _name = 'rent.items'
    _description = 'Rent Items'
    _rec_name = 'name'

    name = fields.Char(string='Name', default='New')
    date = fields.Date('Date', default=date.today())
    order_id = fields.Many2one('sale.order', string='Sale Order')
    partner_id = fields.Many2one('res.partner', string='Vender')
    planning_date = fields.Date(string='Planning Date', default=date.today())
    exp_delivery_date = fields.Date(string='Event Date')
    rent_line_ids = fields.One2many('rent.items.line', 'rent_id', string='Line ids')
    state = fields.Selection(
        [('draft', 'Draft'), ('done', 'Requested'), ('received', 'Received'), ('return', 'Return')], default='draft')

    @api.model
    def create(self, vals):
        if not vals.get('name') or vals['name'] == _('New'):
            vals['name'] = self.env['ir.sequence'].next_by_code('rent.items') or _('New')
        # self.env['sale.order'].browse(vals.get('order_id'))._compute_production_plan()
        a = self.env['sale.order'].browse(vals.get('order_id'))
        a._compute_rent_items()
        a.rent_items_count = 1
        if self.env['rent.items'].search_count([('order_id', '=', vals.get('order_id'))]) >= 1:
            raise ValidationError(_("You cannot request rental items more than one against a sale order."))
        return super(RentItems, self).create(vals)

    def action_create_rent_items(self):
        self.state = 'done'

    def mail_report(self):
        rent_item_list = []
        for line in self.rent_line_ids:
            rent_item_dict = {}
            rent_item_dict['product'] = line.product_id.name
            rent_item_dict['quantity'] = line.quantity
            # rent_item_dict['delivery_date'] = line.exp_production_date
            rent_item_dict['rate'] = line.rate
            rent_item_list.append(rent_item_dict)
        data = {
            'partner_name': self.partner_id.name,
            'event_date': self.exp_delivery_date,
            'rent_item_list': rent_item_list
        }
        # report_template_id = self.env.ref('production_plan_mk.rental_items')._render_qweb_pdf(self.id)[0]
        # data_record = base64.b64encode(report_template_id)
        # ir_values = {
        #     'name': "Rent Items",
        #     'type': 'binary',
        #     'datas': data_record,
        #     'store_fname': data_record,
        #     'mimetype': 'application/x-pdf',
        # }
        # data_id = self.env['ir.attachment'].create(ir_values)
        # template = self.env.ref(
        #     'production_plan_mk.mail_template',
        #     raise_if_not_found=False)
        # template.attachment_ids = [(6, 0, [data_id.id])]
        # email_values = {
        #                 'email_to': self.partner_id.email,
        #                 'subject': 'Rental Items',
        #                 'email_from': self.env.user.email
        #                 }
        # template.send_mail(self.id, email_values=email_values, force_send=True,
        #                    notif_layout='mail.mail_notification_light')
        # template.attachment_ids = [(3, data_id.id)]
        # return True
        # print(self.id)
        # partner_id = self.env['res.partner'].search([])
        # if self.partner_id.id in partner_id:
        #     part = partner_id
        # else:
        #     part = 1
        report_template_id = self.env.ref(
            'production_plan_mk.rental_items').sudo()._render_qweb_pdf(self.id, data)
        data_record = base64.b64encode(report_template_id[0])

        ir_values = {
            'name': "Rent Items",
            'type': 'binary',
            'datas': data_record,
            'store_fname': data_record,
            'mimetype': 'application/x-pdf',
        }

        data_id = self.env['ir.attachment'].create(ir_values)
        template = self.env['mail.template'].search([('id', '=', 1)])
        template.attachment_ids = [(6, 0, [data_id.id])]
        email_values = {'email_to': self.partner_id.email,
                        'subject': 'Rental Items',
                        'email_from': self.env.user.email}
        template.send_mail( self.partner_id.id,email_values=email_values, force_send=True)
        template.attachment_ids = [(3, data_id.id)]
        return True

    def action_receive_rent_items(self):
        location_id = self.env['stock.location'].search([('rent_items_location', '=', True)],limit=1)
        for line in self.rent_line_ids:
            self.env['stock.quant'].sudo().create({
                'product_id': line.product_id.id,
                'location_id': location_id.id,
                'quantity': line.quantity
            })

        self.state = 'received'

    def action_return_rent_items(self):
        location_id = self.env['stock.location'].search([('rent_items_location', '=', True)])
        for ids in self.rent_line_ids:
            quants = self.env['stock.quant'].search([('product_id', '=', ids.product_id.id), ('location_id', '=', location_id.id)])
            for quant in quants:
                quant.sudo().write({'quantity': quant.available_quantity - ids.quantity})
        self.state = 'return'


class RentItemsLine(models.Model):
    _name = 'rent.items.line'
    _description = 'Rent Items Lines'

    rent_id = fields.Many2one('rent.items', string='Rent Items', store=True)
    product_id = fields.Many2one('product.product', string='Product', store=True, domain=[('categ_id.name', '=', 'Assets')])
    # box = fields.Float(string='Box', store=True)
    quantity = fields.Float(string='Quantity', store=True)
    # product_uom_id = fields.Many2one('uom.uom', string='Unit', store=True)
    exp_production_date = fields.Date(string='Expected Delivery Date', default=date.today(), store=True)
    rate = fields.Float(string='Rate')



class Stocklocation(models.Model):
    _inherit = 'stock.location'

    rent_items_location = fields.Boolean(string='Rental Item Location')