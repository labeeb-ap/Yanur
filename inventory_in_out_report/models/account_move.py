import qrcode
import base64
from io import BytesIO
from odoo import models, fields, api, _
from odoo.tools.misc import get_lang
from odoo.exceptions import UserError, ValidationError


# class AccountMoveReport(models.Model):
#     _inherit = 'account.move'
#
#     amount_in_words = fields.Char(string='Amount In Words', compute='_compute_total_amount_in_words')
#     discount_total = fields.Float(string='Total Discount', compute='_compute_discount_total')
#     vehicle_number = fields.Char(string='Vehicle No:')
#     prnt_qr_code = fields.Binary("QR Code", attachment=True, store=True, copy=False)
#     export_type = fields.Selection([('exp_with_pay', 'Export with payment'), ('exp_wo_pay', 'Export without payment')])
#     sez_type = fields.Selection([('sez_with_pay', 'SEZ with payment'),('sez_wo_pay', 'SEZ without payment')])
#     is_ship_diff_address = fields.Boolean(string="Is ship to different address?")
#     ship_gst = fields.Char(string="GST")
#     ship_legal_name = fields.Char(string="Legal Name")
#     ship_add1 = fields.Char(string="Address1")
#     ship_add2 = fields.Char(string="Address2")
#     ship_loc = fields.Char(string="Location")
#     ship_pin = fields.Char(string="PIN Code")
#     ship_st_code = fields.Char(string="State Code")
#     ship_state = fields.Selection([('01', 'Jammu & Kashmir'), ('02', 'Himachal Pradesh'), ('03', 'Punjab'),
#                                         ('04', 'Chandigarh'), ('05', 'Uttranchal'), ('06', 'Haryana'), ('07', 'Delhi'),
#                                         ('08', ' Rajasthan'), ('09', 'Uttar Pradesh'),
#                                         ('10', ' Bihar'), ('11', ' Sikkim'), ('12', 'Arunachal Pradesh'),
#                                         ('13', ' Nagaland'), ('14', ' Manipur'), ('15', ' Mizoram'),
#                                         ('16', ' Tripura'), ('17', ' Meghalaya'), ('18', 'Assam'),
#                                         ('19', ' West Bengal'), ('20', ' Jharkhand'), ('21', ' Orissa'),
#                                         ('22', ' Chhattisgarh'), ('23', 'Madhya Pradesh'), ('24', ' Gujarat'),
#                                         ('25', 'Daman & Diu'), ('26', 'Dadra & Nagar Haveli'),
#                                         ('27', ' Maharashtra'), ('29', ' Karnataka'), ('30', ' Goa'),
#                                         ('31', ' Lakshdweep'), ('32', 'Kerala'), ('33', 'Tamil Nadu'),
#                                         ('34', ' Pondicherry'), ('35', 'Andaman & Nicobar Islands'),
#                                         ('36', ' Telangana'), ('37', ' Andhra Pradesh'), ('38', 'Ladakh'),
#                                         ('97', 'Other Territory'),('96', 'Other Country')], string="State")
#     is_export = fields.Boolean(string="Is Export?")
#     exp_bill_no = fields.Char(string="Shipping Bill No:")
#     exp_bill_date = fields.Date(string="Shipping Bill Date")
#     convert_inr = fields.Float(string="INR Conversion", compute='compute_convert_inr')

    # @api.depends('currency_id')
    # def compute_convert_inr(self):
    #     self.convert_inr = 1 / self.currency_id.rate

    # def einv_compute(self):
    #     res = super(AccountMoveReport, self).einv_compute()
    #     qr = qrcode.QRCode(
    #         version=1,
    #         error_correction=qrcode.constants.ERROR_CORRECT_L,
    #         box_size=20,
    #         border=8,
    #     )
    #     qr.add_data(self.einv_qr_code)
    #     qr.make(fit=True)
    #     img = qr.make_image()
    #     temp = BytesIO()
    #     img.save(temp, format="PNG")
    #     qr_image = base64.b64encode(temp.getvalue())
    #     self.prnt_qr_code = qr_image
    #     return res

    # @api.depends('amount_total', 'currency_id')
    # def _compute_total_amount_in_words(self):
    #     for move in self:
    #         if move.amount_total:
    #             move.amount_in_words = move.currency_id.amount_to_text(move.amount_total)
    #         else:
    #             move.amount_in_words = False

    # @api.depends('invoice_line_ids.discount_amount')
    # def _compute_discount_total(self):
    #     sum = 0
    #     for i in self.invoice_line_ids:
    #         sum += i.discount_amount
    #     self.discount_total = sum

    # def action_post(self):
    #     res = super(AccountMoveReport, self).action_post()
    #     print(self.ship_state, "state")
    #     for i in self.invoice_line_ids:
    #         if len(i.tax_ids) > 1:
    #             raise ValidationError(_('Single Tax value should be given'))
    #
    #         else:
    #             for i in self.invoice_line_ids:
    #                 account = self.env['account.move.line'].search(
    #                     [('move_id', '=', i.move_id.id), ('id', '!=', i.id), ('product_id', '=', i.product_id.id)])
    #                 for k in account:
    #                     for j in i.tax_ids.children_tax_ids:
    #                         if k.tax_line_id.id == j.id:
    #                             if j.tax_group_id.name == 'Cess':
    #                                 i.cess = k.credit
    #                             if j.tax_group_id.name == 'SGST':
    #                                 i.sgst_perc = k.credit
    #                             if j.tax_group_id.name == 'CGST':
    #                                 i.cgst_perc = k.credit
    #                             i.sgst_amount = j.amount
    #                             i.cgst_amount = j.amount
    #                             i.igst_perc = 0.00
    #                             i.igst_amount = 0.00
    #
    #         for d in self.line_ids:
    #             for w in self.invoice_line_ids:
    #                 if d.product_id.id == w.product_id.id:
    #                     if d.tax_line_id:
    #                         if d.tax_line_id.id == w.tax_ids.id:
    #                             w.igst_perc = w.price_total - w.price_subtotal
    #                             w.igst_amount = w.tax_ids.amount
    #                             w.sgst_perc = 0.00
    #                             w.cgst_perc = 0.00
    #                             w.sgst_amount = 0.00
    #                             w.cgst_amount = 0.00
    #                             w.cess = 0.00
    #                             w.cess_amount = 0.00
    #
    #         tax = self.invoice_line_ids.mapped('tax_ids')
    #         lst = []
    #         for t in tax:
    #             line = self.invoice_line_ids.filtered(lambda line: line.tax_ids == t)
    #             sgst = sum(line.mapped('sgst_perc'))
    #             cgst = sum(line.mapped('cgst_perc'))
    #             non_tax_tot = sum(line.mapped('price_unit'))
    #             tax_tot = sum(line.mapped('price_subtotal'))
    #     return res
    #
    # def button_draft(self):
    #     res = super(AccountMoveReport, self).button_draft()
    #     for w in self.invoice_line_ids:
    #         w.igst_perc = 0.00
    #         w.igst_amount = 0.00
    #         w.sgst_perc = 0.00
    #         w.cgst_perc = 0.00
    #         w.sgst_amount = 0.00
    #         w.cgst_amount = 0.00
    #         w.cess = 0.00
    #         w.cess_amount = 0.00
    #     return res

    # @api.onchange('ship_state')
    # def _onchange_ship_state(self):
    #     for rec in self:
    #         if rec.ship_state:
    #             rec.ship_st_code =  rec.ship_state


# class AccountMoveReportLine(models.Model):
#     _inherit = 'account.move.line'

    # discount_amount = fields.Float(string='Discount Amount')
    # sgst_perc = fields.Monetary(string='SGST', copy=False)
    # cgst_perc = fields.Monetary(string='CGST', copy=False)
    # igst_perc = fields.Monetary(string='IGST', copy=False)
    # cess = fields.Monetary(string='Cess', copy=False)
    # sgst_amount = fields.Monetary(string='sgst Rate', copy=False)
    # cgst_amount = fields.Monetary(string='cgst Rate', copy=False)
    # igst_amount = fields.Monetary(string='igst Rate', copy=False)
    # cess_amount = fields.Monetary(string='cess Rate', copy=False)

    # @api.onchange('discount','price_unit','quantity')
    # def onchange_discount_amount(self):
    #     if self.discount:
    #         disc = (self.discount * (self.price_unit * self.quantity)) / 100
    #         self.discount_amount = disc


# class ResPartnerInherit(models.Model):
#     _inherit = 'res.company'
#
#     acc_bank_name = fields.Char(string='Bank Name')
#     bank_branch = fields.Char(string='Bank Branch')
#     acc_number = fields.Char(string='Account Number')
#     bank_ifsc = fields.Char(string='IFSC Code')
#     fssai_no = fields.Char(string='FSSAI No')
#     code_qr = fields.Binary(string='UPI')
#     swift_code = fields.Char(string='Swift Code')
#     currency_remitted = fields.Many2one('res.currency', string='Currency to be remitted')
#     cin_no = fields.Char(string='CIN Number')


# class SaleOrderConfirm(models.Model):
#
#     _inherit = 'sale.order'
#
#     def action_confirm(self):
#         res = super(SaleOrderConfirm, self).action_confirm()
#         for i in self.order_line:
#             if len(i.tax_id) > 1:
#                 raise ValidationError(_('Single Tax value should be given'))
#         return res
#
#     def _prepare_invoice(self):
#         res = super(SaleOrderConfirm, self)._prepare_invoice()
#         print(self.ship_partner_id.state_id.name)
#         if self.ship_partner_id.state_id.name == 'Jammu & Kashmir':
#             res['ship_state'] = '01'
#             res['ship_st_code'] = '01'
#         if self.ship_partner_id.state_id.name == 'Himachal Pradesh':
#             res['ship_state'] = '02'
#             res['ship_st_code'] = '02'
#         if self.ship_partner_id.state_id.name == 'Punjab':
#             res['ship_state'] = '03'
#             res['ship_st_code'] = '03'
#         if self.ship_partner_id.state_id.name == 'Chandigarh':
#             res['ship_state'] = '04'
#             res['ship_st_code'] = '04'
#         if self.ship_partner_id.state_id.name == 'Uttranchal':
#             res['ship_state'] = '05'
#             res['ship_st_code'] = '05'
#         if self.ship_partner_id.state_id.name == 'Haryana':
#             res['ship_state'] = '06'
#             res['ship_st_code'] = '06'
#         if self.ship_partner_id.state_id.name == 'Delhi':
#             res['ship_state'] = '07'
#             res['ship_st_code'] = '07'
#         if self.ship_partner_id.state_id.name == 'Rajasthan':
#             res['ship_state'] = '08'
#             res['ship_st_code'] = '08'
#         if self.ship_partner_id.state_id.name == 'Uttar Pradesh':
#             res['ship_state'] = '09'
#             res['ship_st_code'] = '09'
#         if self.ship_partner_id.state_id.name == 'Bihar':
#             res['ship_state'] = '10'
#             res['ship_st_code'] = '10'
#         if self.ship_partner_id.state_id.name == 'Sikkim':
#             res['ship_state'] = '11'
#             res['ship_st_code'] = '11'
#         if self.ship_partner_id.state_id.name == 'Arunachal Pradesh':
#             res['ship_state'] = '12'
#             res['ship_st_code'] = '12'
#         if self.ship_partner_id.state_id.name == 'Nagaland':
#             res['ship_state'] = '13'
#             res['ship_st_code'] = '13'
#         if self.ship_partner_id.state_id.name == 'Manipur':
#             res['ship_state'] = '14'
#             res['ship_st_code'] = '14'
#         if self.ship_partner_id.state_id.name == 'Mizoram':
#             res['ship_state'] = '15'
#             res['ship_st_code'] = '15'
#         if self.ship_partner_id.state_id.name == 'Tripura':
#             res['ship_state'] = '16'
#             res['ship_st_code'] = '16'
#         if self.ship_partner_id.state_id.name == 'Meghalaya':
#             res['ship_state'] = '17'
#             res['ship_st_code'] = '17'
#         if self.ship_partner_id.state_id.name == 'Assam':
#             res['ship_state'] = '18'
#             res['ship_st_code'] = '18'
#         if self.ship_partner_id.state_id.name == 'West Bengal':
#             res['ship_state'] = '19'
#             res['ship_st_code'] = '19'
#         if self.ship_partner_id.state_id.name == 'Jharkhand':
#             res['ship_state'] = '20'
#             res['ship_st_code'] = '20'
#         if self.ship_partner_id.state_id.name == 'Orissa':
#             res['ship_state'] = '21'
#             res['ship_st_code'] = '21'
#         if self.ship_partner_id.state_id.name == 'Chhattisgarh':
#             res['ship_state'] = '22'
#             res['ship_st_code'] = '22'
#         if self.ship_partner_id.state_id.name == 'Madhya Pradesh':
#             res['ship_state'] = '23'
#             res['ship_st_code'] = '23'
#         if self.ship_partner_id.state_id.name == 'Gujarat':
#             res['ship_state'] = '24'
#             res['ship_st_code'] = '24'
#         if self.ship_partner_id.state_id.name == 'Daman & Diu':
#             res['ship_state'] = '25'
#             res['ship_st_code'] = '25'
#         if self.ship_partner_id.state_id.name == 'Dadra & Nagar Haveli':
#             res['ship_state'] = '26'
#             res['ship_st_code'] = '26'
#         if self.ship_partner_id.state_id.name == 'Maharashtra':
#             res['ship_state'] = '27'
#             res['ship_st_code'] = '27'
#         if self.ship_partner_id.state_id.name == 'Karnataka':
#             res['ship_state'] = '29'
#             res['ship_st_code'] = '29'
#         if self.ship_partner_id.state_id.name == 'Goa':
#             res['ship_state'] = '30'
#             res['ship_st_code'] = '30'
#         if self.ship_partner_id.state_id.name == 'Lakshadweep':
#             res['ship_state'] = '31'
#             res['ship_st_code'] = '31'
#         if self.ship_partner_id.state_id.name == 'Kerala':
#             res['ship_state'] = '32'
#             res['ship_st_code'] = '32'
#         if self.ship_partner_id.state_id.name == 'Tamil Nadu':
#             res['ship_state'] = '33'
#             res['ship_st_code'] = '33'
#         if self.ship_partner_id.state_id.name == 'Pondicherry':
#             res['ship_state'] = '34'
#             res['ship_st_code'] = '34'
#         if self.ship_partner_id.state_id.name == 'Andaman & Nicobar Islands':
#             res['ship_state'] = '35'
#             res['ship_st_code'] = '35'
#         if self.ship_partner_id.state_id.name == 'Telangana':
#             res['ship_state'] = '36'
#             res['ship_st_code'] = '36'
#         if self.ship_partner_id.state_id.name == 'Andhra Pradesh':
#             res['ship_state'] = '37'
#             res['ship_st_code'] = '37'
#         if self.ship_partner_id.state_id.name == 'Ladakh':
#             res['ship_state'] = '38'
#             res['ship_st_code'] = '38'
#         if self.ship_partner_id.state_id.name == 'Other Territory':
#             res['ship_state'] = '97'
#             res['ship_st_code'] = '97'
#         if self.ship_partner_id.state_id.name == 'Other Country':
#             res['ship_state'] = '96'
#             res['ship_st_code'] = '96'
#
#
#         res['is_ship_diff_address'] = self.is_ship_to
#         res['ship_legal_name'] = self.ship_partner_id.name
#         res['ship_add1'] = self.ship_partner_id.street
#         res['ship_add2'] = self.ship_partner_id.street2
#         res['ship_loc'] = self.ship_partner_id.city
#         res['ship_pin'] = self.ship_partner_id.zip
#         # res['ship_state'] = self.ship_partner_id.state_id.id
#         print(res)
#         print(res['invoice_origin'])
#         print(self.ship_partner_id.state_id.name)
#         account_id = self.env['account.move'].sudo().search([('invoice_origin', '=', res['invoice_origin'])])
#         print(account_id)
#         # res._onchange_ship_state()
#
#         return res
#
#
#
#
# class ProductQR(models.Model):
#     _inherit = "account.move"
#     qr_code = fields.Binary("QR Code", attachment=True, store=True)
#
#     @api.onchange('default_code')
#     def generate_qr_code(self):
#         qr = qrcode.QRCode(
#             version=1,
#             error_correction=qrcode.constants.ERROR_CORRECT_L,
#             box_size=10,
#             border=4,
#         )
#         qr.add_data(self.default_code)
#         qr.make(fit=True)
#         img = qr.make_image()
#         temp = BytesIO()
#         img.save(temp, format="PNG")
#         qr_image = base64.b64encode(temp.getvalue())
#         self.qr_code = qr_image


