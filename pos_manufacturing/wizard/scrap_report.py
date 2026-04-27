import time
import json
from datetime import date, datetime
import io
from odoo import models, fields, api, _
from odoo.tools import date_utils
from odoo.exceptions import Warning
import base64
from odoo.http import request

try:
    from odoo.tools.misc import xlsxwriter
except ImportError:
    import xlsxwriter


class DailySales(models.TransientModel):
    _name = "scrap.report"
    _description = "Scrap Report"

    from_date = fields.Date(string='From Date')
    to_date = fields.Date(string='To Date')

    def scrap_report_xlsx(self):
        company_id = self.env.company.id
        company_name = self.env.company.name

        if self.from_date > self.to_date:
            raise Warning(_("From Date Is Greater Than To Date!"))
        else:
            condition = '''AND DATE(ss.date_done) BETWEEN '%s' AND '%s'
                            AND ss.company_id = %s
                            GROUP BY ss.product_id, pt.name, ss.scrap_qty, pt.list_price, ss.feedback, DATE(ss.date_done), ss.state
                            ''' % (self.from_date, self.to_date, company_id)
            query = """SELECT DATE(ss.date_done) AS date_done, ss.product_id, pt.name, SUM(ss.scrap_qty) AS qty, SUM(pt.list_price) AS price, ss.feedback, ss.state
                        FROM stock_scrap ss
                        LEFT JOIN product_product pp ON ss.product_id = pp.id
                        LEFT JOIN product_template pt ON pp.product_tmpl_id = pt.id
                        WHERE ss.state = 'done'
                        %s
                    """ % condition

        self._cr.execute(query)
        scrap_ids = self.env.cr.dictfetchall()
        print(scrap_ids)

        rows = []
        lens = []
        for i in scrap_ids:
            rows.append({
                'date':i['date_done'],
                'product':i['name'],
                'scrap_qty':i['qty'],
                'price':i['price'],
                'feedback':i['feedback'],
                'state':i['state']
            })
            lens.append({'data':{
                        'date':i['date_done']

            }})
        print('rows',rows)
        print('lens',lens)

        no_dup =[]
        for p in lens:
            if p['data'] not in no_dup:
                no_dup.append(p['data'])
        print('no_dup',no_dup)


        inv=[]
        for v in no_dup:
            d_date = v['date']
            vals=[]
            for t in rows:
                if t['date'] == d_date:
                    vals.append({
                        'date':t['date'],
                        'product':t['product'],
                        'scrap_qty':t['scrap_qty'],
                        'price':t['price'],
                        'feedback':t['feedback'],
                        'state':t['state'],
                    })
            inv.append({
                'date':d_date,
                'vals':vals

            })
        inv.sort(key=lambda x: x['date'])
        print('final',inv)
        
        data = {
            'from_date': self.from_date.strftime('%d-%m-%Y'),
            'to_date': self.to_date.strftime('%d-%m-%Y'),
            'company_name':company_name,
            'result':inv
        }

        return {
            'type': 'ir.actions.report',
            'data': {'model': 'scrap.report',
                     'options': json.dumps(data, default=date_utils.json_default),
                     'output_format': 'xlsx',
                     'report_name': 'Scrap Report',
                     },
            'report_type': 'xlsx',
        }

    def get_xlsx_report(self, data, response):
        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})
        underline = workbook.add_format({'bold': True, 'underline': True})
        sheet = workbook.add_worksheet('Customer Order')
        bold = workbook.add_format({'bold': True})

        print('1111111111111111111111111111111111111111111111')

        format_1 = workbook.add_format(
            {'font_size': 25, 'bold': True, 'align': 'center', 'valign': 'vcenter', 'bg_color': '#BDB76B', 'border': 1})
        format_1.set_font_name('Times New Roman')
        format_3 = workbook.add_format(
            {'bold': True, 'align': 'center', 'valign': 'center', 'bg_color': '#FFFF00', 'border': 1})
        format_4 = workbook.add_format(
            {'bold': True, 'align': 'center', 'valign': 'vcenter', 'bg_color': '#FFC1C1', 'font_size': 13, 'border': 1})
        format_5 = workbook.add_format(
            {'bold': True, 'align': 'right', 'valign': 'right', 'bg_color': '#FFFF00', 'font_size': 13, 'border': 1})

        sheet.set_column('D:D', 15)
        sheet.set_column('C:C', 35)
        sheet.set_column('E:E', 14)
        sheet.set_column('G:G', 30)
        sheet.set_column('F:F', 18)
        sheet.set_column('B:B', 14)
        sheet.set_column('H:H', 20)
        sheet.set_column('A:A', 12)
        sheet.set_column('J:J', 25)
        sheet.set_column('I:I', 20)

        sheet.merge_range('E3:G4', 'YA-NUR RESTAURANT', format_1)
        sheet.merge_range('D7:H8', 'MONTHLY SUMMARY SPOILAGE REPORT', format_1)
        # sheet.merge_range('D10:D10', 'DATE', format_3)
        # sheet.merge_range('E10:E10', 'ITEM', format_3)
        # sheet.merge_range('F10:F10', 'QUANTITY', format_3)
        # sheet.merge_range('G10:G10', 'UNIT PRICE', format_3)
        # sheet.merge_range('H10:H10', 'AMOUNT', format_3)
        # sheet.merge_range('I10:I10', 'REASON', format_3)
        # sheet.merge_range('J10:J10', 'CHEF SIGN', format_3)
        # sheet.merge_range('K10:E10', 'MOD SIGN', format_3)


        print('222222222222222222222222222222222222222')

        sheet.write(9, 3, 'FROM DATE :', bold)
        sheet.write(5, 6,data['company_name'], format_3)
        sheet.write(9, 4, data['from_date'], bold)
        sheet.write(9, 6, 'TO DATE :', bold)
        sheet.write(9, 7, data['to_date'], bold)
        sheet.write(10, 1, 'DATE', format_3)
        sheet.write(10, 2, 'ITEM', format_3)
        sheet.write(10, 3, 'QUANTITY', format_3)
        sheet.write(10, 4, 'UNIT PRICE', format_3)
        sheet.write(10, 5, 'AMOUNT', format_3)
        sheet.write(10, 6, 'REASON', format_3)
        sheet.write(10, 7, 'CHEF SIGN', format_3)
        sheet.write(10, 8, 'MOD SIGN', format_3)


        print('3333333333333333333333333333333333333333')


        row = 11  # Start writing from row 11
        product_data = {}

        for item in data['result']:
            date = item['date']
            for i in item['vals']:
                product = i.get('product')
                if product:
                    scrap_qty = i.get('scrap_qty', 0)
                    price = i.get('price', 0)
                    feedback = i.get('feedback', '')

                    if product not in product_data:
                        product_data[product] = {'scrap_qty': scrap_qty, 'price': price, 'feedback': feedback,'state': feedback}
                        print(product_data[product])
                    else:
                        product_data[product]['scrap_qty'] += scrap_qty
                        product_data[product]['price'] += price

        total_value = 0
        for product, values in product_data.items():
            sheet.write(row, 1, date, bold)
            sheet.write(row, 2, product, bold)
            sheet.write(row, 3, values['scrap_qty'], bold)
            sheet.write(row, 4, values['price'], bold)
            sheet.write(row, 5, values['scrap_qty'] * values['price'], bold)
            total_value += values['scrap_qty'] * values['price']
            sheet.write(row, 6, values['feedback'], bold)
            row += 1

        sheet.write(row+2, 4, 'TOTAL :', bold)
        sheet.write(row+2, 5,total_value , bold)

        workbook.close()
        output.seek(0)
        response.stream.write(output.read())
        output.close()



