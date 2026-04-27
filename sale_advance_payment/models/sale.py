from odoo import models, api, fields, _
from odoo.exceptions import ValidationError

class sale_order(models.Model):
    _inherit = 'sale.order'

    adv_payment_ids = fields.Many2many('account.payment', string="Advance Payment", copy=False)
    advance_amount = fields.Float(string='Advance Amount')
    posted_advance_amount = fields.Monetary(string='Posted Advance Amount', compute='_compute_posted_advance_amount', store=True, currency_field='currency_id')
    due_amount = fields.Monetary(string='Due Amount', compute='_compute_posted_advance_amount', store=True, currency_field='currency_id')
    @api.depends('adv_payment_ids.state', 'adv_payment_ids.amount')
    def _compute_posted_advance_amount(self):
        for order in self:
            order.posted_advance_amount = sum(
                payment.amount for payment in order.adv_payment_ids if payment.state == 'posted'
            )
            order.due_amount = order.amount_total - order.posted_advance_amount
            # order.amount_total -= order.posted_advance_amount

    def action_view_adv_payments(self):
        action = self.env.ref('account.action_account_payments').sudo().read()[0]
        action['domain'] = [('id', 'in', self.adv_payment_ids.ids)]
        action['context'] = {'create': 0}
        return action

    def btn_advance_payment(self):
        ctx = {'default_payment_type': 'inbound',
               'default_partner_type': 'customer',
               'search_default_inbound_filter': 1,
               'res_partner_search_mode': 'customer',
               'default_partner_id': self.partner_id.id,
               'default_ref': self.name,
               'default_currency_id': self.currency_id.id}
        return {'name': _("Advance Payment"),
                'type': 'ir.actions.act_window',
                'view_mode': 'form',
                'res_model': 'account.payment',
                'target': 'new',
                'view_id': self.env.ref('sale_advance_payment.view_sale_advance_account_payment_form').id,
                'context': ctx}


class account_payment(models.Model):
    _inherit = 'account.payment'

    create_in_state_sale = fields.Selection([('draft', 'Draft'),
                                             ('confirm', 'Confirm')],
                                            default='confirm',
                                            string="Payment Status")
    total_advance = fields.Float(string='Total Advance')

    def create_sale_adv_payment(self):
        if self.amount <= 0.0:
            raise ValidationError(_("The payment amount cannot be negative or zero."))
        if self.create_in_state_sale == 'confirm':
            self.action_post()
        if self.env.context.get('active_id'):
            sale_id = self.env['sale.order'].browse(self.env.context.get('active_id'))
            sale_id.write({'adv_payment_ids': [(4, self.id)],
                           'advance_amount': self.amount
                           })
        return True
