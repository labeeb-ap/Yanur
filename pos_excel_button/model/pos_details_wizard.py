from odoo import models, fields
import io
import base64
import xlsxwriter
from collections import defaultdict
from datetime import datetime

class PosDetailsWizard(models.TransientModel):
    _inherit = 'pos.details.wizard'

    file_data = fields.Binary("Excel File", readonly=True)
    file_name = fields.Char("File Name", readonly=True)



    def export_excel(self):
        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})
        worksheet = workbook.add_worksheet("Daily Sales Report")

        # --- Define formats ---
        main_heading = workbook.add_format({
            'bold': True,
            'font_size': 18,
            'font_color': 'black',
            'bg_color': '#D9D993',
            'align': 'center',
            'valign': 'vcenter',
            'border': 0
        })

        sub_heading = workbook.add_format({
            'bold': False,
            'font_size': 12,
            'font_color': 'black',
            'align': 'center',
            'valign': 'vcenter',
            'border': 1,
            'text_wrap': False
        })

        header_format = workbook.add_format({
            'bold': True,
            'font_color': 'white',
            'bg_color': '#D99393',  # Ruddy Pink
            'align': 'center',
            'valign': 'vcenter'
        })

        money_format = workbook.add_format({'num_format': '#,##0.00', 'align': 'right'})
        date_format = workbook.add_format({'num_format': 'dd/mm/yyyy', 'align': 'center'})
        summary_label = workbook.add_format({
            'bold': True,
            'bg_color': '#FFD966',
            'align': 'right'
        })
        summary_amount = workbook.add_format({
            'bold': True,
            'bg_color': '#FFD966',
            'num_format': '#,##0.00',
            'align': 'right'
        })

        # --- Row heights ---
        worksheet.set_row(0, 30)
        worksheet.set_row(1, 20)
        worksheet.set_row(3, 20)

        # --- Main heading ---
        worksheet.merge_range('A1:F1', 'Yanur Restaurant - Daily Sales Report', main_heading)

        # --- Subheading ---
        outlet_name = ', '.join([c.name for c in self.pos_config_ids]) if self.pos_config_ids else 'All Outlets'
        start_date_str = self.start_date.strftime('%d/%m/%Y') if self.start_date else ''
        end_date_str = self.end_date.strftime('%d/%m/%Y') if self.end_date else ''
        date_range = f"From :  {start_date_str}   To :  {end_date_str}"
        worksheet.merge_range('A2:F2', f"Outlet: {outlet_name} | {date_range}", sub_heading)

        # --- Table headers ---
        headers = ["Date", "Cash", "Card", "Bank Transfer", "Discount", "Total Sales"]
        for col, header in enumerate(headers):
            worksheet.write(3, col, header, header_format)
            worksheet.set_column(col, col, 18)

        # --- Fetch POS orders ---
        domain = [
            ('date_order', '>=', self.start_date),
            ('date_order', '<=', self.end_date),
        ]
        if self.pos_config_ids:
            domain.append(('config_id', 'in', self.pos_config_ids.ids))
        orders = self.env['pos.order'].search(domain)

        # --- Group orders by date ---
        daily_totals = defaultdict(lambda: {'cash': 0, 'card': 0, 'bank': 0, 'discount': 0, 'total': 0})

        for order in orders:
            cash_total = card_total = bank_total = discount_total = 0

            # Payments
            for payment in order.payment_ids:
                method_name = payment.payment_method_id.name.lower()
                if payment.payment_method_id.is_cash_count:
                    cash_total += payment.amount
                elif method_name in ['card', 'credit card', 'debit card']:
                    card_total += payment.amount
                elif 'bank' in method_name:
                    bank_total += payment.amount
                else:
                    card_total += payment.amount  # fallback

            # Discount calculation
            order_discount = sum(
                (line.price_unit * line.qty) * (line.discount / 100.0)
                for line in order.lines
            )
            discount_total += order_discount

            # Order total
            order_total = sum(line.price_subtotal_incl for line in order.lines)

            # Group by date
            order_date = order.date_order.date()
            daily_totals[order_date]['cash'] += cash_total
            daily_totals[order_date]['card'] += card_total
            daily_totals[order_date]['bank'] += bank_total
            daily_totals[order_date]['discount'] += discount_total
            daily_totals[order_date]['total'] += order_total

        # --- Write rows ---
        row = 4
        total_cash = total_card = total_bank = total_discount = total_sales = 0
        for order_date, values in sorted(daily_totals.items()):
            worksheet.set_row(row, 18)
            worksheet.write_datetime(row, 0, order_date, date_format)
            worksheet.write(row, 1, values['cash'], money_format)
            worksheet.write(row, 2, values['card'], money_format)
            worksheet.write(row, 3, values['bank'], money_format)
            worksheet.write(row, 4, values['discount'], money_format)
            worksheet.write(row, 5, values['total'], money_format)

            total_cash += values['cash']
            total_card += values['card']
            total_bank += values['bank']
            total_discount += values['discount']
            total_sales += values['total']
            row += 1

        # --- Summary row ---
        worksheet.set_row(row, 20)
        worksheet.write(row, 0, 'TOTAL', summary_label)
        worksheet.write(row, 1, total_cash, summary_amount)
        worksheet.write(row, 2, total_card, summary_amount)
        worksheet.write(row, 3, total_bank, summary_amount)
        worksheet.write(row, 4, total_discount, summary_amount)
        worksheet.write(row, 5, total_sales, summary_amount)

        workbook.close()
        output.seek(0)
        self.file_data = base64.b64encode(output.read())
        self.file_name = "POS_Daily_Sales_Report.xlsx"

        return {
            'type': 'ir.actions.act_url',
            'url': f'/web/content/?model=pos.details.wizard&id={self.id}&field=file_data&filename_field=file_name&download=true',
            'target': 'self',
        }