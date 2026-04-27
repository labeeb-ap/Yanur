from odoo import models, fields


# class CompanyPosition(models.Model):
#     _inherit = 'res.company'
#     _description = 'Company'
#
#     manager = fields.Many2one('res.users', string='Manager')
#     chef = fields.Many2one('res.users', string='Chef')

class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    mail = fields.Boolean(string="Mail", copy=False)

    # state = fields.Selection(selection_add=[
    #     ('sent',),
    #     ('purchase',),
    #
    #     ('approved', 'Approved')], )

    # def action_rfq_send(self):
    #     res = super().action_rfq_send()
    #     print(self.mail)
    #
    #     return res

    # def action_approval(self):
    #     self.state == 'approved'
    #     # res = super(PurchaseOrder).create(self.action_rfq_send)
    #     # return res

    # return {
    #     'type': 'ir.actions.act_window',
    #     'view_type': 'form',
    #     'view_mode': 'form',
    #     'res_model': 'mail.compose.message',
    #     'target': 'new',
    # }


# class PurchaseOrderEmail(models.TransientModel):
#     _inherit = 'mail.compose.message'
#
#     mail_id = fields.Many2one('purchase.order', string='Mail')

    # def action_send_mail(self):
    #     res = super().action_send_mail()
    #     context = {
    #         'default_mail_id': self.id,
    #     }
        # self.mail_id.mail =True

        # # if x:
        # self.mail_id.mail = True
        # return res
