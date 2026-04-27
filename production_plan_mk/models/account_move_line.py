from odoo import api, fields, models, _
from odoo.exceptions import  UserError


class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'

    box = fields.Float(string='Box')
    box_count = fields.Float(string='Box Count')
    product_expiration = fields.Char(string='Shelf Life', store=True, default='18 Months')

    @api.onchange('product_id', 'box')
    def _onchange_box_quantity(self):
        if self.product_id:
            self.box_count = self.product_id.product_tmpl_id.box
            if self.box != 0:
                self.quantity = self.product_id.product_tmpl_id.box * self.box

    @api.onchange('product_id', 'quantity')
    def _onchange_quantity_box(self):
        if self.box != 0 and self.product_id.product_tmpl_id.box != 0:
            if self.quantity != self.product_id.product_tmpl_id.box * self.box:
                raise UserError(_('The Box: %s and Quantity: %s of %s are not matching. please set box.', self.box,
                                  self.quantity, self.name))
