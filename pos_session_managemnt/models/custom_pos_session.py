from odoo import models, fields, api, _

class PosSession(models.Model):
    _inherit = 'res.users'

    pos_session_ids = fields.Many2many('pos.config',string="POS configs")


class PosConfig(models.Model):
    _inherit = 'pos.config'

#
# class PosPaymentMethod(models.Model):
#     _inherit = 'pos.payment.method'
#
#
#
# class PosCategory(models.Model):
#     _inherit = "pos.category"