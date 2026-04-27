from odoo import models, fields, api, _


class CrmLeadCustomisation(models.Model):
    _inherit = 'crm.lead'

    event_date = fields.Date(string='Event Date')
    venue = fields.Char(string='Venue')
    # per_head_price = fields.Monetary(string='Per Head Price',currency_field='company_currency')
    # min_no_person = fields.Float(string="No Of Person")


    def action_new_quotation(self):
        res = super(CrmLeadCustomisation, self).action_new_quotation()
        res['context'].update({
            'default_exp_delivery_date': self.event_date,
            'default_venue': self.venue,
            'default_email': self.email_from,
            # 'default_price_amount':self.per_head_price,
            # 'default_price_amount_min_person':self.min_no_person
        })
        return res

class ContactIc(models.Model):
    _inherit = 'res.partner'

    ic_number = fields.Char(string ="IC Number")










