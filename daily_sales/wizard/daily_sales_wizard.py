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
    _name = "daily.sales"
    _description = "Daily Sales"

    from_date = fields.Date(string='From Date')
    to_date = fields.Date(string='To Date')

    def daily_sales_xlsx(self):
        company_name = self.env.company.name
        company_id = self.env.company.id

        if self.from_date > self.to_date:
            raise Warning("From Date Is Greater Than To Date!")
        else:
            condition = """AND aml.date BETWEEN '%s' AND '%s' AND aml.company_id = '%s'
                            GROUP BY aml.date, account_account.account_type, account_account.name,aj.name,aj.type
                        """ % (self.from_date, self.to_date,company_id)
            query = """SELECT aml.date, SUM(aml.debit) AS debit, account_account.account_type, account_account.name,aj.name as journal_name,aj.type as journal_type
                        FROM account_move_line aml
                        LEFT JOIN account_move am ON aml.move_id = am.id
                        LEFT JOIN account_account ON aml.account_id = account_account.id
                        LEFT JOIN account_journal as aj on aml.journal_id = aj.id
                        WHERE am.state = 'posted' AND account_account.account_type IS NOT NULL
                        %s
                        ORDER BY aml.date ASC
                    """ % condition

            self._cr.execute(query)
            acnt_move_ids = self.env.cr.dictfetchall()

            invoice_ids = self.env['account.move'].search([
                ('state', '=', 'posted'),
                ('invoice_origin', '!=', False),
                ('pax_qty', '!=', None),
                ('date', '>=', self.from_date),
                ('date', '<=', self.to_date)
            ])

            rows = []
            lens = []

            for i in acnt_move_ids:
                rows.append({
                    'date': i['date'],
                    'debit': i['debit'],
                    'account_type': i['account_type'],
                    'journal_type': i['journal_type']
                })
                lens.append({'data': {'date': i['date']}})

            rows_pax = []
            lens_pax = []
            for j in invoice_ids:
                rows_pax.append({
                    'date': j.date,
                    'amount_total': j.amount_total,
                    'pax_qty': j.pax_qty,
                    'payment_state': j.payment_state
                })
                lens_pax.append({'data': {'date': j['date']}})

            no_dup = []
            for p in lens:
                if p['data'] not in no_dup:
                    no_dup.append(p['data'])

            no_dup_pax = []
            for p in lens_pax:
                if p['data'] not in no_dup_pax:
                    no_dup_pax.append(p['data'])


            inv = []
            for v in no_dup:
                d_date = v['date']
                vals = []
                for t in rows:
                    if t['date'] == d_date:
                        vals.append({
                            'debit': t['debit'],
                            'account_type': t['account_type'],
                            'journal_type': t['journal_type'],
                            # 'pax_qty': None,
                            # 'payment_state': None
                        })
                    inv.append({'date': d_date, 'vals': vals})

            print(inv)

            unique_inv = []
            seen_date = set()
            for item in inv:
                date = item['date']
                if date not in seen_date:
                    unique_inv.append(item)
                    seen_date.add(date)

            print(unique_inv)

            inv = unique_inv

            inv_pax = []
            for k in no_dup_pax:
                d_date = k['date']
                vals_pax = []
                for t in rows_pax:
                    if t['date'] == d_date:
                        vals_pax.append({
                            'amount_total': t['amount_total'],
                            'pax_qty': t['pax_qty'],
                            'payment_state': t['payment_state']
                        })
                inv_pax.append({'date': d_date, 'vals_pax': vals_pax})

            # Remove duplicates from inv_pax based on 'date'
            unique_inv_pax = []
            seen_dates = set()
            for item in inv_pax:
                date = item['date']
                if date not in seen_dates:
                    unique_inv_pax.append(item)
                    seen_dates.add(date)

            inv_pax = unique_inv_pax


            data = {
                'from_date': self.from_date.strftime('%d-%m-%Y'),
                'to_date': self.to_date.strftime('%d-%m-%Y'),
                'company_name': company_name,
                'result': inv,
                'result_pax': inv_pax
            }

        return {
            'type': 'ir.actions.report',
            'data': {
                'model': 'daily.sales',
                'options': json.dumps(data, default=date_utils.json_default),
                'output_format': 'xlsx',
                'report_name': 'Daily Sales Report',
            },
            'report_type': 'xlsx'
        }

    def get_xlsx_report(self, data, response):
        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})
        underline = workbook.add_format({'bold': True, 'underline': True})
        sheet = workbook.add_worksheet('Customer Order')
        bold = workbook.add_format({'bold': True})

        print('1111111111111111111111111111111111111111111111')

        format_1 = workbook.add_format(
            {'font_size': 25, 'bold': True, 'align': 'left', 'valign': 'vleft', 'bg_color': '#BDB76B', 'border': 1})
        format_1.set_font_name('Times New Roman')
        format_3 = workbook.add_format(
            {'bold': True, 'align': 'center', 'valign': 'center', 'bg_color': '#CD5C5C', 'border': 1})
        format_4 = workbook.add_format(
            {'bold': True, 'align': 'center', 'valign': 'vcenter', 'bg_color': '#FFC1C1', 'font_size': 13, 'border': 1})
        format_5 = workbook.add_format(
            {'bold': True, 'align': 'right', 'valign': 'right', 'bg_color': '#FFFF00', 'font_size': 13, 'border': 1})

        sheet.set_column('D:D', 18)
        sheet.set_column('C:C', 14)
        sheet.set_column('E:E', 19)
        sheet.set_column('G:G', 20)
        sheet.set_column('F:F', 25)
        sheet.set_column('B:B', 14)
        sheet.set_column('H:H', 25)
        sheet.set_column('A:A', 12)
        sheet.set_column('J:J', 25)
        sheet.set_column('I:I', 25)

        sheet.merge_range('A1:D2', 'YA-NUR RESTAURANT', format_1)
        sheet.merge_range('H1:J2', 'DAILY SALES REPORT', format_1)
        sheet.merge_range('E1:E2', '', bold)
        sheet.merge_range('F1:F2', '', bold)
        sheet.merge_range('G1:G2', '', bold)
        sheet.merge_range('B5:I5', 'DAILY', format_4)
        sheet.merge_range('A6:A7', 'DATE', format_3)
        sheet.merge_range('B6:B7', 'PAX', format_3)
        sheet.merge_range('C6:C7', 'CASH', format_3)
        sheet.merge_range('D6:D7', 'CARD', format_3)
        # sheet.merge_range('D6:D7', 'TRANSFER', format_3)
        sheet.merge_range('E6:E7', 'TRANSFER', format_3)
        sheet.merge_range('F6:F7', 'CREDIT SALES', format_3)
        sheet.merge_range('G6:G7', 'DISCOUNT/VOUCHER', format_3)
        sheet.merge_range('H6:H7', 'INDOOR/OUTDOOR', format_3)
        sheet.merge_range('I6:I7', 'ALACARTE', format_3)
        sheet.merge_range('J5:J7', 'TOTAL SALES', format_3)


        sheet.write(3, 3, 'FROM DATE :', bold)
        sheet.write(3, 4, data['from_date'], bold)
        sheet.write(3, 6, 'TO DATE :', bold)
        sheet.write(3, 7, data['to_date'], bold)
        sheet.write(3, 0, 'OUTLET :', bold)
        sheet.write(3, 1, data['company_name'], underline)
        sheet.write(4, 0, '', format_4)


        totals_by_date = {}

        for item in data['result']:
            date = item['date']
            cash_total = 0
            card_total = 0
            transfer_total = 0
            cheque_total = 0
            discount = 0
            voucher = 0
            total_discount = 0
            indoor_outdoor = 0
            pax = 0
            for i in item['vals']:
                if i['journal_type'] == 'cash':
                    cash_total += i['debit']
                if i['account_type'] == 'card':
                    card_total += i['debit']
                if i['account_type'] == 'bank':
                    transfer_total += i['debit']
                if i['account_type'] == 'cheque':
                    cheque_total += i['debit']
                if i['account_type'] == 'discount':
                    discount += i['debit']
                if i['account_type'] == 'voucher':
                    voucher += i['debit']
                total_discount = discount + voucher

            total_sales = cash_total + indoor_outdoor + card_total + transfer_total + cheque_total
            totals_by_date[date] = {'cash_total': cash_total, 'card_total': card_total,
                                    'transfer_total': transfer_total, 'cheque_total': cheque_total,
                                    'total_discount': total_discount,
                                    'indoor_outdoor': indoor_outdoor, 'pax': pax, 'total_sales': total_sales}

        for item in data['result_pax']:
            date = item['date']
            vals_pax = item['vals_pax']
            if date in totals_by_date:
                totals_by_date[date]['pax'] = sum(val['pax_qty'] for val in vals_pax)
                totals_by_date[date]['indoor_outdoor'] = sum(val['amount_total'] for val in vals_pax)


        pax_total = 0
        cash_total = 0
        card_total = 0
        transfer_total = 0
        cheque_total = 0
        discount_total = 0
        indoor_outdoor_total = 0
        alacarte_total = 0
        sales_total = 0
        row = 0
        for row, date in enumerate(sorted(totals_by_date)):
            totals = totals_by_date[date]

            sheet.write(row + 7, 0, date, bold)

            sheet.write(row + 7, 1, totals['pax'], bold)
            pax_total += totals['pax']

            sheet.write(row + 7, 2, totals['cash_total'], bold)
            cash_total += totals['cash_total']

            sheet.write(row + 7, 3, totals['card_total'], bold)
            card_total += totals['card_total']

            sheet.write(row + 7, 4, totals['transfer_total'], bold)
            transfer_total += totals['transfer_total']

            sheet.write(row + 7, 5, totals['cheque_total'], bold)
            cheque_total += totals['cheque_total']

            sheet.write(row + 7, 6, totals['total_discount'], bold)
            discount_total += totals['total_discount']

            sheet.write(row + 7, 7, totals['indoor_outdoor'], bold)
            indoor_outdoor_total += totals['indoor_outdoor']

            sheet.write(row + 7, 8, totals['total_sales'] - totals['indoor_outdoor'], bold)
            alacarte = totals['total_sales'] - totals['indoor_outdoor']
            alacarte_total += alacarte


            sheet.write(row + 7, 9, totals['total_sales'], bold)
            sales_total += totals['total_sales']

        sheet.write(row + 10, 0, 'Total', format_5)
        sheet.write(row + 10, 1, pax_total, format_5)
        sheet.write(row + 10, 2, cash_total, format_5)
        sheet.write(row + 10, 3, card_total, format_5)
        sheet.write(row + 10, 4, transfer_total, format_5)
        sheet.write(row + 10, 5, cheque_total, format_5)
        sheet.write(row + 10, 6, discount_total, format_5)
        sheet.write(row + 10, 7, indoor_outdoor_total, format_5)
        sheet.write(row + 10, 8, alacarte_total, format_5)
        sheet.write(row + 10, 9, sales_total, format_5)

        workbook.close()
        output.seek(0)
        response.stream.write(output.read())
        output.close()



