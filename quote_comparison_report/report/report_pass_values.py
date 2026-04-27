from odoo import models, _
from odoo.exceptions import ValidationError


class ReportQuoteComparisonReport(models.AbstractModel):
    _name = 'report.quote_comparison_report.quote_comparison_report_template'

    def _get_report_values(self, docids, data=None):
        report = self.env['ir.actions.report']._get_report_from_name(
            'quote_comparison_report.quote_comparison_report_template')
        obj = self.env[report.model].browse(docids)

        rfq = []
        terms = []
        for rf in obj:
            # if rf.state == 'draft':
            rfq.append({
                'rfq_name': rf.name,
                'rfq_vendor': rf.partner_id.name,
                'rfq_terms': rf.notes,
            })
            terms.append({
                'rfq_name': rf.name,
                'receipt_date': rf.date_planned.strftime('%d/%m/%Y') if rf.date_planned else '',
                'payment_terms': rf.payment_term_id.name if rf.payment_term_id.name else '',
            })

        rfq.sort(key=lambda x: x['rfq_name'])
        terms.sort(key=lambda x: x['rfq_name'])

        product_list = []
        vendor_list = []
        values = []
        product_vendor = []
        line_length = []
        for record in obj.order_line:
            # if record.state == 'draft':
            line_length.append(record.id)
            product_list.append({'data': {
                'item_list_id': record.product_id.id,
                'item_name': record.name,
            }})
            vendor_list.append({'data': {
                'vendor_id': record.partner_id.id,
                'vendor_name': record.partner_id.name,
            }})
            values.append({
                'item_list_id': record.product_id.id,
                'item_name': record.name,
                'item_price': record.price_unit,
                'item_quantity': record.product_qty,
                'item_vendor': record.partner_id.id,
            })
            product_vendor.append({'data': {
                'product_id': record.product_id.id,
                'vendor_id': record.partner_id.id,
            }})

        if len(line_length) == 0:
            raise ValidationError(_("There Is Nothing To Print"))

        no_dup_product = []
        for p in product_list:
            if p['data'] not in no_dup_product:
                no_dup_product.append(p['data'])

        no_dup_vendor = []
        for v in vendor_list:
            if v['data'] not in no_dup_vendor:
                no_dup_vendor.append(v['data'])
        vendor_length = len(no_dup_vendor)

        no_dup_product_vendor = []
        for pv in product_vendor:
            if pv['data'] not in no_dup_product_vendor:
                no_dup_product_vendor.append(pv['data'])

        inv_color = []
        for product_c in no_dup_product:
            product_item_id = product_c['item_list_id']
            price_color_list = []
            for val_pro in values:
                if val_pro['item_list_id'] == product_item_id:
                    price_color_list.append(val_pro['item_price'])
            inv_color.append({
                "pro_id": product_item_id,
                "list_price": min(price_color_list),
            })

        inv = []
        for i in no_dup_product_vendor:
            item_id = i['product_id']
            vend_id = i['vendor_id']
            pro_name = ''
            price_list = []
            quantity_list = []
            for val in values:
                if val['item_list_id'] == item_id and val['item_vendor'] == vend_id:
                    pro_name = val['item_name']
                    price_list.append(val['item_price'])
                    quantity_list.append({
                        'price': val['item_price'],
                        'quant': val['item_quantity'],
                    })
            qy = 0
            for q in quantity_list:
                if q['price'] == min(price_list):
                    qy = q['quant']
            inv.append({
                "label": pro_name,
                "quantity": qy,
                "vendor_id": vend_id,
                "pro_id": item_id,
                "list_price": min(price_list),
            })

        return {
            'docs': obj,
            'products': no_dup_product,
            'vendors': no_dup_vendor,
            'l': vendor_length,
            'vals': inv,
            'color': inv_color,
            'purchase': rfq,
            'terms': terms,
        }
