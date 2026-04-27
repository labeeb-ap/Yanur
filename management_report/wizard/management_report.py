import time
import json
from datetime import date
import io
import calendar

from odoo import models, fields, api, _
from odoo.tools import date_utils
from odoo.exceptions import Warning
from datetime import datetime
from dateutil.relativedelta import relativedelta

import base64
from odoo.http import request

try:
    from odoo.tools.misc import xlsxwriter
except ImportError:
    import xlsxwriter


class ManagementReport(models.TransientModel):
    _name = "management.report"
    _description = "Management Report"

    from_date = fields.Date(string='From Date')
    to_date = fields.Date(string='To Date')
    company_ids = fields.Many2many('res.company',string='Company')

    def management_report_xlsx(self):
        company_id = self.company_ids.ids
        if self.from_date > self.to_date:
            raise Warning("From Date Is Greater Than To Date!")
        else:
            company_ids_str = ', '.join(str(company_id) for company_id in company_id)
            condition = """AND am.date >= '%s' and am.date <= '%s'""" % (
                self.from_date, self.to_date)

            query = """SELECT sum(aml.balance) as balance,sum(aml.debit) as debit, sum(aml.credit) as credit,cbl.date_from,cbl.date_to,
                        aag.name as group_name, aa.name AS account_name, aml.date, cbl.planned_amount,
                        rc.name as rc_name, aat.name as account_type, aaa.name as analytic_name, aaa.sale
                        FROM account_move_line as aml
                        LEFT JOIN crossovered_budget_lines AS cbl ON aml.analytic_account_id = cbl.analytic_account_id and aml.date between cbl.date_from and cbl.date_to
                        LEFT JOIN account_analytic_account AS aaa ON cbl.analytic_account_id = aaa.id
                        LEFT JOIN account_analytic_group AS aag ON cbl.analytic_group = aag.id
                        LEFT JOIN account_move as am on aml.move_id = am.id
                        LEFT JOIN res_company as rc on aml.company_id = rc.id
                        LEFT JOIN account_budget_post AS abp ON cbl.general_budget_id = abp.id
                        LEFT JOIN account_budget_rel AS abr ON abr.budget_id = abp.id
                        LEFT JOIN account_account AS aa ON abr.account_id = aa.id
                        LEFT JOIN account_account_type AS aat ON aa.user_type_id = aat.id
                        WHERE aml.analytic_account_id IS NOT NULL AND aml.account_id = abr.account_id AND aml.company_id IN (%s) %s
                        GROUP BY (aaa.sale_profit,rc.name, aag.name, aaa.name,aag.id, aml.date,cbl.planned_amount, aa.name, aaa.sale, aat.name,cbl.date_from,cbl.date_to)""" % (
            company_ids_str, condition)

            profit_query = """SELECT am.date, SUM(aml.balance) AS balance, aat.internal_group, aa.name, rc.name, aaa.royalty, aml.company_id,sum(aml.debit) as debit,sum(aml.credit) as credit
                            FROM account_move_line aml
                            LEFT JOIN account_account aa ON aml.account_id = aa.id 
                            LEFT JOIN account_account_type aat ON aa.user_type_id = aat.id
                            LEFT JOIN account_move am ON aml.move_id = am.id
                            LEFT JOIN res_company as rc on aml.company_id = rc.id
                            LEFT JOIN account_analytic_account AS aaa ON aml.analytic_account_id = aaa.id
                            WHERE aat.internal_group IN ('expense', 'income') AND aml.company_id IN (%s) %s
                            GROUP BY am.date, aat.internal_group, aa.name, rc.name, aaa.royalty, aml.company_id""" % (
            company_ids_str, condition)

            self._cr.execute(profit_query)
            profit_result = self.env.cr.dictfetchall()
            self._cr.execute(query)
            acnt_move_ids = self.env.cr.dictfetchall()

            if not acnt_move_ids:
                raise Warning("Nothing to Print")



            rows = []
            lens = []

            for i in acnt_move_ids:
                rows.append({
                    'rc_name': i['rc_name'],
                    # 'aml_analytic_account_id': i['aml_analytic_account_id'],
                    'account_name': i['account_name'],
                    'planned_amount': i['planned_amount'],
                    'account_type': i['account_type'],
                    'debit': i['debit'],
                    'credit': i['credit'],
                    'sale': i['sale'],
                    'group_name': i['group_name'],
                    # 'practical': i['practical'],
                    # 'group_id': i['group_id'],
                    'analytic_name': i['analytic_name'],
                    'balance': i['balance'],
                    'date': i['date'],
                })
                lens.append({
                    'data': {
                        'date': i['date'],
                    }
                })

            rows_pr = []
            lens_pr = []

            for i in profit_result:
                rows_pr.append({
                    'balance': i['balance'],
                    'date': i['date'],
                    'internal_group': i['internal_group'],
                    'name': i['name'],
                    'royalty': i['royalty'],
                    'debit': i['debit'],
                    'credit': i['credit']

                })
                lens_pr.append({
                    'data': {
                        'date': i['date'],
                    }
                })


            no_dup = []
            for p in lens:
                if p['data'] not in no_dup:
                    no_dup.append(p['data'])

            no_dup_pr = []
            for p in lens_pr:
                if p['data'] not in no_dup_pr:
                    no_dup_pr.append(p['data'])


            inv_pr = []
            for v in no_dup_pr:
                t_date = v['date']
                vals_pr = []
                for value in rows_pr:
                    if t_date == value['date']:
                        vals_pr.append({
                             'balance': value['balance'],
                            'date': value['date'],
                            'internal_group': value['internal_group'],
                            'name': value['name'],
                            'royalty': value['royalty'],
                            'debit': value['debit'],
                            'credit': value['credit']

                        })
                inv_pr.append({'date': t_date, 'vals_pr': vals_pr})


            inv = []

            # # Retrieve the company names from the data
            for v in no_dup:
                d_date = v['date']
                vals = []
                for i in rows:
                    if d_date == i['date']:
                        vals.append({
                            'rc_name': i['rc_name'],
                            # 'aml_analytic_account_id': i['aml_analytic_account_id'],
                            'account_name': i['account_name'],

                            'planned_amount': i['planned_amount'],
                            'date': i['date'],
                            'account_type': i['account_type'],

                            'debit': i['debit'],
                            'sale': i['sale'],
                            'credit': i['credit'],
                            'group_name': i['group_name'],
                            # 'practical': i['practical'],
                            # 'group_id': i['group_id'],
                            'analytic_name': i['analytic_name'],
                            'balance': i['balance'],
                        })
                inv.append({'date': d_date,'vals': vals})


            data = {
                'from_date': self.from_date.strftime('%d-%m-%Y'),
                'to_date': self.to_date.strftime('%d-%m-%Y'),
                'company_id': company_id,
                'result': inv,
                'result_pr': inv_pr,
            }



            return {
                'type': 'ir.actions.report',
                'data': {
                    'model': 'management.report',
                    'options': json.dumps(data, default=date_utils.json_default),
                    'output_format': 'xlsx',
                    'report_name': 'MGT Budget Report',
                },
                'report_type': 'xlsx'
            }

    def get_xlsx_report(self, data, response):
        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})
        underline = workbook.add_format({'bold': True, 'underline': True})
        sheet = workbook.add_worksheet('Customer Order')
        bold = workbook.add_format({'bold': True})
        bold_1 = workbook.add_format({'bold': True, 'align': 'center', 'valign': 'vcenter'})

        format_1 = workbook.add_format(
            {'font_size': 13, 'bold': True, 'align': 'center', 'valign': 'vcenter', 'bg_color': '#BDB76B', 'border': 1})
        format_1.set_font_name('Times New Roman')

        format_3 = workbook.add_format(
            {'font_size': 30, 'bold': True, 'align': 'center', 'valign': 'center', 'bg_color': '#BDB76B', 'border': 1})

        format_4 = workbook.add_format(
            {'bold': True, 'align': 'center', 'valign': 'vcenter', 'bg_color': '#FFC1C1', 'font_size': 13, 'border': 1})
        format_5 = workbook.add_format(
            {'bold': True, 'align': 'left', 'valign': 'vleft', 'bg_color': '#FFFF00', 'font_size': 11, 'border': 1})
        format_6 = workbook.add_format(
            {'bold': True, 'align': 'left', 'valign': 'left', 'bg_color': '#FFFF00', 'font_size': 11, 'border': 1})


        sheet.set_column('D:D', 28)
        sheet.set_column('C:C', 25)
        sheet.set_column('E:E', 28)
        sheet.set_column('G:G', 25)
        sheet.set_column('F:F', 25)
        sheet.set_column('B:B', 25)
        sheet.set_column('K:K', 25)
        sheet.set_column('L:L', 25)
        sheet.set_column('M:M', 25)
        sheet.set_column('N:N', 25)
        sheet.set_column('O:O', 25)
        sheet.set_column('P:P', 25)
        sheet.set_column('Q:Q', 25)
        sheet.set_column('R:R', 28)
        sheet.set_column('S:S', 25)
        sheet.set_column('T:T', 25)
        sheet.set_column('U:U', 25)
        sheet.set_column('V:V', 28)
        sheet.set_column('W:W', 25)
        sheet.set_column('X:X', 26)
        sheet.set_column('Y:Y', 25)
        sheet.set_column('Z:Z', 25)
        sheet.set_column('H:H', 25)
        sheet.set_column('A:A', 55)
        sheet.set_column('J:J', 25)
        sheet.set_column('I:I', 25)

        start_date = datetime.strptime(data['from_date'], '%d-%m-%Y').date()
        end_date = datetime.strptime(data['to_date'], '%d-%m-%Y').date()

        start_month = start_date.month
        start_year = start_date.year
        end_month = end_date.month
        end_year = end_date.year



        current_month = start_month
        current_year = start_year
        col_index = 1

        months = []
        month_columns = []
        while (current_year, current_month) <= (end_year, end_month):
            month_name = datetime.strptime(str(current_month), '%m').strftime('%B').upper()

            months.append((current_year, month_name,col_index))
            month_columns.append({'month_name':month_name,'col_index':col_index})

            current_month += 1
            col_index += 2

            if current_month > 12:
                current_month = 1
                current_year += 1

        for year, month_name, col_index in months:
            budgeted_column_index = chr(
                ord('A') + col_index)  # Convert col_index to corresponding column letter for budgeted column
            actual_column_index = chr(
                ord('A') + col_index + 1)  # Convert col_index to corresponding column letter for actual column

            yanur_cell_end = f'{actual_column_index}3'
            mgt_cell_end = f'{actual_column_index}7'

            budgeted_cell_start = f'{budgeted_column_index}8'
            budgeted_cell_end = f'{budgeted_column_index}9'
            actual_cell_start = f'{actual_column_index}8'
            actual_cell_end = f'{actual_column_index}9'

            # Rest of your code to populate the sheet

            merge_range_start = 'A1'
            mgt_start = 'A4'

            sheet.merge_range(merge_range_start + ':' + yanur_cell_end, 'YA-NUR RESTAURANT', format_3)
            sheet.merge_range(mgt_start + ':' + mgt_cell_end, f'MGT REPORT {year}', format_3)
            sheet.merge_range('A8:A9','PARTICULARS', bold)
            sheet.merge_range(budgeted_cell_start + ':' + budgeted_cell_end, f'BUDGETED {month_name} {year}', bold_1)
            sheet.merge_range(actual_cell_start + ':' + actual_cell_end, f'ACTUAL {month_name} {year}', bold_1)

        net_profit = {}

        cols = col_index + 1

        for group_data in data['result_pr']:
            group_vals_pr = group_data['vals_pr']
            for item_pr in group_vals_pr:
                item_date = datetime.strptime(item_pr['date'], '%Y-%m-%d').date()
                month_key = item_date.strftime('%B').upper()

                if start_date <= item_date <= end_date:
                    company_name = item_pr['name']
                    internal_group = item_pr['internal_group']
                    balance = abs(item_pr['balance'])
                    debit = item_pr['debit']
                    credit = item_pr['credit']
                    is_royalty = item_pr['royalty']

                    net_profit.setdefault(company_name, {}).setdefault(month_key,
                                                                       {'net_pro_bal': 0, 'royalty_income': 0,
                                                                        'income': 0, 'expense': 0})

                    if internal_group == 'expense':
                        net_profit[company_name][month_key]['expense'] += balance
                    if internal_group == 'income':
                        net_profit[company_name][month_key]['income'] += credit - debit



                    if is_royalty:
                        net_profit[company_name][month_key]['royalty_income'] += balance

                    net_profit[company_name][month_key]['net_pro_bal'] = net_profit[company_name][month_key]['income'] - net_profit[company_name][month_key]['expense']




        group_names = {}
        group_names_accou = {}

        for group_data in data['result']:
            group_vals = group_data['vals']

            for item in group_vals:
                item_date = datetime.strptime(group_data['date'], '%Y-%m-%d').date()

                item_month = item_date.strftime('%B').upper()

                if start_date <= item_date <= end_date:
                    group_name = item['group_name']
                    rc_name = item['rc_name']
                    account_name = item['account_name']
                    planned_amount = item['planned_amount']
                    balance = item['balance']

                    if item['sale']:
                        group_names.setdefault(group_name, {}).setdefault(rc_name, {}).setdefault(item_month,{'planned_amount': 0,'balance': 0})
                        if item_month not in group_names[group_name][rc_name]:
                            group_names[group_name][rc_name][item_month] = {'planned_amount': 0, 'balance': 0}
                        group_names[group_name][rc_name][item_month]['planned_amount'] = planned_amount
                        group_names[group_name][rc_name][item_month]['balance'] += balance
                    else:
                        group_names_accou.setdefault(group_name, {}).setdefault(account_name, {}).setdefault(item_month,{'planned_amount': 0,'balance': 0})
                        group_names_accou[group_name][account_name][item_month]['planned_amount'] = planned_amount
                        group_names_accou[group_name][account_name][item_month]['balance'] += balance



        row  = 9
        col = 0
        month_list = []
        group_total_planned_amount_sales = 0
        group_total_balance_sales = 0

        for group_name, items_sales in group_names.items():
            sheet.write(row, col, group_name, format_6)
            for col_index_2 in range(1, cols + 1):
                sheet.write(row, col + col_index_2, None, format_6)
            row += 1

            for company_name, item_sales_group in items_sales.items():
                sheet.write(row, col, company_name, bold)

                for month_index in range(1, 13):
                    month_name = calendar.month_name[month_index].upper()
                    col_index = None

                    for month_dict in month_columns:
                        if month_dict['month_name'] == month_name:
                            col_index = month_dict['col_index']
                            break



                    if month_name in item_sales_group:
                        item_group = item_sales_group[month_name]
                        sales_planned = item_group['planned_amount']
                        sales_balance = item_group['balance']
                        sheet.write(row, col + col_index, sales_planned, bold)
                        sheet.write(row, col + col_index + 1, sales_balance, bold)
                        group_total_planned_amount_sales += sales_planned
                        group_total_balance_sales += sales_balance

                        month_list.append({
                            'col_index': col_index,
                            'sales_planned': sales_planned,
                            'sales_balance': sales_balance,
                        })

                row += 1

        sum_sales_planned = {}
        sum_sales_balance = {}


        for item in month_list:
            col_index = item['col_index']
            if col_index not in sum_sales_planned:
                sum_sales_planned[col_index] = 0
            if col_index not in sum_sales_balance:
                sum_sales_balance[col_index] = 0

            sum_sales_planned[col_index] += item['sales_planned']
            sum_sales_balance[col_index] += item['sales_balance']

        for col_index in sum_sales_planned:
            sheet.write(row, col, f'TOTAL OF {group_name}', bold)
            sheet.write(row, col_index, sum_sales_planned[col_index], bold)
            sheet.write(row, col_index + 1, sum_sales_balance[col_index], bold)
        row += 1


        sheet.write(row, 0, 'NET PROFIT', format_6)
        for col_1 in range(1, cols + 1):
            sheet.write(row, col_1, None, format_6)

        row += 1

        col = 0
        if net_profit:
            net_pro = []
            royal_in = []
            total_net_pro = 0

            for company_name, items_profit in net_profit.items():
                sheet.write(row, 0, company_name, bold)

                for month_index in range(1, 13):
                    month_name = calendar.month_name[month_index].upper()
                    col_index = None

                    for month_dict in month_columns:
                        if month_dict['month_name'] == month_name:
                            col_index = month_dict['col_index']
                            break

                    if month_name in items_profit:
                        item_group = items_profit[month_name]
                        net_pro_bal = item_group['net_pro_bal']
                        royalty = item_group['royalty_income']
                        sheet.write(row, col_index, 0, bold)

                        sheet.write(row, col_index + 1, net_pro_bal, bold)
                        total_net_pro += net_pro_bal
                        net_pro.append({
                            'net_pro': net_pro_bal,
                            'col_index': col_index,
                            'royalty_income': royalty
                        })
                        royal_in.append({
                            'col_index': col_index,
                            'royalty_income': royalty
                        })

                row += 1

            sum_net_balance = {}
            sum_roya = {}

            for item in net_pro:
                col_index_net = item['col_index']
                net_pro_value = item['net_pro']

                if col_index_net not in sum_net_balance:
                    sum_net_balance[col_index_net] = 0
                sum_net_balance[col_index_net] += net_pro_value

            for item_roy in royal_in:
                col_index_roy = item_roy['col_index']
                royalty = item_roy['royalty_income']

                if col_index_roy not in sum_roya:
                    sum_roya[col_index_roy] = 0
                sum_roya[col_index_roy] += royalty

            for col_index_net in sum_net_balance:
                sheet.write(row, col, f'TOTAL OF {group_name}', bold)
                sheet.write(row, col_index_net, 0, bold)
                sheet.write(row, col_index_net + 1, sum_net_balance[col_index_net], bold)

            row += 1
            sheet.write(row, 0, 'NET PROFIT/LOSS %', bold)

            for col_index, items in sum_sales_balance.items():
                if col_index in sum_net_balance:
                    itemss = sum_net_balance[col_index]
                    net_profit_loss = (itemss / items) * 100
                    rounded_net_profit_loss = round(net_profit_loss, 2)
                    sheet.write(row, col_index, 0, bold)
                    sheet.write(row, col_index + 1, rounded_net_profit_loss, bold)

            row += 1

        col_2 = 0

        group_total_planned_amount_exp = 0
        group_total_balance_exp = 0

        account_total = {}


        for group_name, items_accou in group_names_accou.items():
            sheet.write(row, col, group_name, format_6)
            for col_index_2 in range(1, cols + 1):
                sheet.write(row, col + col_index_2, None, format_6)
            row += 1
            sum_exp_planned = {}
            sum_exp_balance = {}

            group_total_planned_amount_group = 0
            group_total_balance_group = 0

            for account_name, item_accou_group in items_accou.items():
                sheet.write(row, col, account_name, bold)

                for month_index in range(1, 13):
                    month_name = calendar.month_name[month_index].upper()
                    col_index = None

                    for month_dict in month_columns:
                        if month_dict['month_name'] == month_name:
                            col_index = month_dict['col_index']
                            break

                    if month_name in item_accou_group:
                        item_group = item_accou_group[month_name]
                        exp_planned = item_group['planned_amount']
                        exp_balance = item_group['balance']

                        sheet.write(row, col + col_index, exp_planned, bold)
                        sheet.write(row, col + col_index + 1, exp_balance, bold)

                        group_total_planned_amount_exp += exp_planned
                        group_total_balance_exp += exp_balance
                        group_total_planned_amount_group += exp_planned
                        group_total_balance_group += exp_balance

                        if col_index not in sum_exp_planned:
                            sum_exp_planned[col_index] = 0
                        if col_index not in sum_exp_balance:
                            sum_exp_balance[col_index] = 0

                        sum_exp_planned[col_index] += exp_planned
                        sum_exp_balance[col_index] += exp_balance



                row += 1


            for col_index in sum_exp_planned:
                print('col_index',col_index)
                sheet.write(row, col, f'TOTAL OF {account_name}', bold)
                sheet.write(row, col_index, sum_exp_planned[col_index], bold)
                sheet.write(row, col_index + 1, sum_exp_balance[col_index], bold)
            row += 1

            for col_index, items in sum_exp_balance.items():

                if col_index not in account_total:
                    account_total[col_index] = 0
                account_total[col_index] += sum_exp_balance[col_index]

            print('account_total', account_total)

        # Move to the next row for the next group

                # Write total sales and balances for each group
        sheet.write(row + 1, col_2, 'GRAND TOTAL OF EXPENSES', format_6)
        sheet.write(row + 2, col_2, 'CONSOLIDATED NET PROFIT/(LOSS) OF COMPANY', format_6)
        sheet.write(row + 3, col_2, 'CONSOLIDATED NET PROFIT/(LOSS) % OF COMPANY', format_6)
        sheet.write(row + 4, col_2, 'ROYALTY INCOME', format_6)
        sheet.write(row + 5, col_2, 'NET PROFIT AFTER ROYALTY', format_6)
        sheet.write(row + 6, col_2, 'SENIOR MANAGEMENT INCENTIVE', format_6)
        sheet.write(row + 7, col_2, 'GRAND NET PROFIT', format_6)

        for col_2 in range(1, cols + 1):
            sheet.write(row + 1, col_2, None, format_6)
            sheet.write(row + 2, col_2, None, format_6)
            sheet.write(row + 3, col_2, None, format_6)
            sheet.write(row + 4, col_2, None, format_6)
            sheet.write(row + 5, col_2, None, format_6)
            sheet.write(row + 6, col_2, None, format_6)
            sheet.write(row + 7, col_2, None, format_6)



        for col_index, total in account_total.items():
            print('col_index',col_index)
            sheet.write(row + 1, col_index + 1, total, format_6)

            if col_index in sum_net_balance:
                net_tot = sum_net_balance[col_index]
                consolidate_net = total - net_tot
                sheet.write(row + 2, col_index + 1, consolidate_net, format_6)
                consolidated_net_per = (consolidate_net / net_tot) * 100
                consolidate_round = round(consolidated_net_per, 2)

                sheet.write(row + 3, col_index + 1,consolidate_round, format_6)

        for col_index, total in sum_roya.items():

            if col_index in sum_roya:
                royal = sum_roya[col_index]
                sheet.write(row + 4, col_index + 1,royal, format_6)

            if col_index in sum_net_balance:
                net_tot = sum_net_balance[col_index]

                net_pro_after_roy = royal + net_tot
                sheet.write(row + 5, col_index + 1,net_pro_after_roy, format_6)
                senior_man_inc = net_pro_after_roy * 0.1
                sheet.write(row + 6, col_index + 1,senior_man_inc, format_6)
                grand_net_profit = net_tot - senior_man_inc
                sheet.write(row + 7, col_index + 1,grand_net_profit, format_6)


        workbook.close()
        output.seek(0)
        response.stream.write(output.read())
        output.close()

