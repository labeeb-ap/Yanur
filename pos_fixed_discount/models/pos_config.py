from odoo import api, fields, models, _
from odoo.exceptions import ValidationError

class POSConfig(models.Model):
    _inherit = 'pos.config'

    discount_amt = fields.Float(string="Discount Amount")

    @api.constrains('discount_pc','discount_amt')
    def _check_discount_percentage(self):
        for rec in self:
            if rec.discount_pc < 0.0 or rec.discount_pc > 100:
                raise ValidationError(_('Discount percentage should be between 1-100'))
            if rec.discount_amt < 0.0:
                raise ValidationError(_('Discount Amount should be greater than 0'))
