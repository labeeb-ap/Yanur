from odoo import api, fields, models, _
from odoo.exceptions import ValidationError

class CurrencyType(models.Model):
    _name = 'currency.type'
    _description = 'Indian Currency'
    _rec_name = 'value'

    value = fields.Float('Value')
#     counter_close_ids = fields.One2many('currency.close','currency_id')
#
# class CurrencyTypeClosse(models.Model):
#     _name = 'currency.close'
#
#     value = fields.Float('Value')
#     currency_id = fields.Many2one('currency.type')




