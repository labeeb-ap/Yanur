from odoo import models


class CustomAccountInvoicePdf(models.AbstractModel):
    _name = 'report.sales_invoice_print.account_invoice_custom_report'

    def _get_report_values(self, docids, data=None):
        report = self.env['ir.actions.report']._get_report_from_name(
            'sales_invoice_print.account_invoice_custom_report')
        docs = self.env[report.model].browse(docids)

        def add_row(pax=0, description='', quantity=0, price=0, total=0, main_value=0):
            return {
                'pax': pax,
                'description': description,
                'quantity': quantity,
                'price': price,
                'total': total,
                'main_value': main_value
            }

        for doc in docs:
            rows = [
                add_row(doc.price_amount_min, doc.event_id.event_type or '', doc.pax_qty, doc.price_amount,
                        doc.pax_qty * doc.price_amount, 1)
            ]

            rows += [add_row(description=line.product_id.name or '') for line in doc.invoice_line_ids if
                     not line.is_rental_item]

            order_id = (doc.invoice_line_ids.mapped('sale_line_ids.order_id') or [None])[0]
            eo_number = ''
            venue_name = ''
            sales_man_name = ''
            if order_id:
                eo_number = order_id.name
                venue_name = order_id.venue
                sales_man_name = order_id.sales_man.name if order_id.sales_man else ''
                if order_id.total_pax_com:
                    rows += [
                        add_row(order_id.total_pax_com, 'COMPLEMENTARY', order_id.total_pax_com,
                                order_id.complementry_price_per_pax,
                                order_id.total_pax_com * order_id.complementry_price_per_pax, 1)
                    ]
                    if order_id.remarks_com:
                        for line in order_id.remarks_com.splitlines():
                            rows.append(add_row(description=line))
                if order_id.total_pax_food:
                    rows += [
                        add_row(order_id.total_pax_food, 'FOOD TASTING', order_id.total_pax_food,
                                order_id.food_price_per_pax,
                                order_id.total_pax_food * order_id.food_price_per_pax, 1)
                    ]
                    if order_id.remarks_food:
                        for line in order_id.remarks_food.splitlines():
                            rows.append(add_row(description=line))
                if order_id.rental_item_ids:
                    rows += [
                        add_row(description='Additional Remarks', main_value=1),
                        add_row(description='ADDITIONAL :')
                    ]
                    rows += [add_row(description=item.rental_product.name or '') for item in order_id.rental_item_ids]
            return {
                'docs': doc,
                'vals': rows,
                'eo_number': eo_number,
                'venue_name': venue_name,
                'sales_man_name': sales_man_name
            }
