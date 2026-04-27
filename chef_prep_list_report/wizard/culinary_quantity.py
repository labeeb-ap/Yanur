from odoo import api, fields, models, _
from odoo.exceptions import Warning


class CulinaryQuantity(models.Model):
    _name = 'culinary.quantity'

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
            order_ids = self.env['sale.order'].search([
                ('exp_delivery_date', '>=', date_from),
                ('exp_delivery_date', '<=', date_to),
                ('company_id', '=', company_id),
            ])

        product_list = []
        for i in order_ids:
            pax_num = i.price_amount_min
            for j in i.order_line:
                quantity = j.product_uom_qty
                product_qty = int(pax_num) * int(quantity)
                product_dict = {
                    'product_id' : j.product_id.id,
                    'product_name' : j.product_id.name,
                    'product_quantity' : product_qty
                }
                product_list.append(product_dict)


        # product_final_dict = {}
        # for pro_dict in product_list:
        #     if pro_dict['product_id'] in product_final_dict:
        #         product_final_dict[pro_dict['product_id']].appened()

        aggregated_quantities = {}

        print(product_list)
        for product in product_list:
            product_id = product['product_id']
            quantity = product['product_quantity']

            # Check if product_id already exists in the dictionary
            if product_id in aggregated_quantities:
                # If exists, add the quantity
                aggregated_quantities[product_id]['product_quantity'] += quantity
            else:
                # If not exists, initialize with current product data
                aggregated_quantities[product_id] = product

        # Convert aggregated quantities dictionary back to a list of dictionaries
        new_product_list = list(aggregated_quantities.values())

        print(new_product_list)
        data = {
            'ids': self.ids,
            'model': self._name,
            'objet_list': new_product_list,
            'company_name': self.company_id.name,
            'start': self.from_date.strftime("%d-%m-%Y"),
            'end': self.to_date.strftime("%d-%m-%Y"),
        }
        return self.env.ref('chef_prep_list_report.culinary_list_report_pdf').report_action(self, data=data)
