from odoo import api, fields, models, _
from odoo.exceptions import Warning


class EventOrderSummary(models.Model):
    _name = 'event.order.summary'

    from_date = fields.Date(string="From Date")
    to_date = fields.Date(string="To Date")
    company_id = fields.Many2one('res.company', string="Company", default=lambda self: self.env.company)

    def print_pdf_report(self):
        date_from = self.from_date.strftime('%Y-%m-%d 00:00:00')
        date_to = self.to_date.strftime('%Y-%m-%d 23:59:59')
        company_id = self.env.company.id
        if self.from_date > self.to_date:
            raise Warning(_("From Date is GreaterThan To Date"))
        else:
            filter_cdtn = '''where so.state = 'sale' and
                 so.date_order between '%s' AND '%s' and so.company_id = '%s'
                 ''' % (date_from, date_to, company_id)

        query = '''select so.id so_id,so.name so_id,so.event_title so_event_title,so.partner_id so_partner_id,
                    res.name so_partner_name,so.time_yanur so_time_yanur,so.sales_man so_sales_man_id,re.name so_sales_man_name,so.date_order so_date_order,
                    so.exp_delivery_date so_exp_delivery_date,so.total_pax so_total_pax,so.price_per_pax so_price_per_pax,
                    so.additional_amount so_additional_amount,so.amount_total so_amount_total,so.venue so_venue,so.state so_st,so.total_pax_food so_total_pax_food,
					so.food_price_per_pax so_food_price_per_pax,so.remarks_food so_remarks_food,so.food_venue so_food_venue,so.events_date_food so_events_date_food,
					so.event_time_food so_event_time_food,
				    so.total_pax_com so_total_pax_com,so.complementry_price_per_pax so_complementry_price_per_pax,so.remarks_com so_remarks_com,so.venue_com so_venue_com,
					so.events_date_complementory so_events_date_complementory,so.event_time_complementory so_event_time_complementory
                    from sale_order so
                    left join res_partner res on so.partner_id = res.id
                    left join res_partner re on so.sales_man = re.id  %s''' % (filter_cdtn)

        self._cr.execute(query)
        sale_ids = self._cr.dictfetchall()

        grand_total = 0
        additional_amount = 0
        total_pax_com = 0
        total_amount_com = 0
        total_pax_food = 0
        for i in sale_ids:
            grand_total += i['so_amount_total']
            additional_amount += i['so_additional_amount']
            total_pax_com += i['so_total_pax_com'] if i['so_total_pax_com'] else 0
            total_pax_food += i['so_total_pax_food'] if i['so_total_pax_food'] else 0

        objet_list = []

        for i in sale_ids:
            vals = {'name': i['so_id'], 'event_title': i['so_event_title'], 'customer': i['so_partner_name'],
                    'time_yanur': i['so_time_yanur'], 'sales_man_name': i['so_sales_man_name'],
                    'date_order': i['so_date_order'], 'exp_delivery_date': i['so_exp_delivery_date'],
                    'total_pax': i['so_total_pax'], 'price_per_pax': i['so_price_per_pax'],
                    'additional_amount': i['so_additional_amount'], 'amount_total': i['so_amount_total'],
                    'venue': i['so_venue'], 'total_pax_food': i['so_total_pax_food'],
                    'food_price_per_pax': i['so_food_price_per_pax'],
                    'remarks_food': i['so_remarks_food'], 'food_venue': i['so_food_venue'],
                    'events_date_food': i['so_events_date_food'], 'event_time_food': i['so_event_time_food'],
                    'total_pax_com': i['so_total_pax_com'], 'complementry_price_per_pax': i['so_complementry_price_per_pax'],
                    'events_date_complementory': i['so_events_date_complementory'],
                    'event_time_complementory': i['so_event_time_complementory'],

                    'event_amount_comp': i['so_total_pax_com'] * i['so_complementry_price_per_pax'] if i['so_total_pax_com'] and i[
                        'so_complementry_price_per_pax'] else 0,

                    'event_amount': i['so_total_pax_food'] * i['so_food_price_per_pax'] if i['so_total_pax_food'] and i[
                        'so_food_price_per_pax'] else 0
                    }

            objet_list.append(vals)

        total_amount_com = 0

        for j in objet_list:
            total_amount_com += j['event_amount_comp']

        total_amount_food = 0

        for k in objet_list:
            total_amount_food += k['event_amount']

        data = {
            'ids': self.ids,
            'model': self._name,
            'objet_list': objet_list,

            'company_name': self.company_id.name,
            'com_street': self.company_id.street,
            'com_street2': self.company_id.street2,
            'com_city': self.company_id.city,
            'com_state': self.company_id.state_id.name,
            'com_zip': self.company_id.zip,
            'com_country': self.company_id.country_id.name,
            'com_phone': self.company_id.phone,
            'com_email': self.company_id.email,

            'additional_amount': additional_amount,
            'grand_total': grand_total,
            'total_pax_com': total_pax_com,
            'total_amount_food': total_amount_food,

            'total_amount_com': total_amount_com,
            'total_pax_food': total_pax_food,
            'start': self.from_date.strftime("%d-%m-%Y"),
            'end': self.to_date.strftime("%d-%m-%Y"),
        }

        return self.env.ref('sale_order_summary_report.event_order_report_pdf').report_action(self, data=data)

