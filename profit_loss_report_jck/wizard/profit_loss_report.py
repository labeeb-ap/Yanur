import time
import json
import datetime
from datetime import date, datetime,timedelta
import io
from odoo import models, fields, api, _
from odoo.tools import date_utils
from odoo.exceptions import Warning
from dateutil.relativedelta import relativedelta
import calendar

import base64
from odoo.http import request

try:
    from odoo.tools.misc import xlsxwriter
except ImportError:
    import xlsxwriter


class ProfitLoss(models.TransientModel):
    _name = "profit.loss"
    _description = "Profit Loss Report"

    from_date = fields.Date(string='From Date', default='2023-10-01')

    to_date = fields.Date(string='To Date',default='2023-10-31')
    company_ids = fields.Many2many('res.company', string='Company',default=[(6, 0, [1])])

    def profit_loss_xlsx(self):
        company_id = self.company_ids.ids

        if self.from_date > self.to_date:
            raise Warning("From Date Is Greater Than To Date!")
        else:
            company_ids_str = ', '.join(str(company_id) for company_id in company_id)
            condition = """AND aml.date >= '%s' and aml.date <= '%s'""" % (
                self.from_date, self.to_date)

            previous_day = self.from_date - timedelta(days=1)

            product_condition = """AND DATE(svl.create_date) >= '%s' and DATE(svl.create_date) <= '%s'""" % (
                previous_day, self.to_date)

            query = """SELECT 
                        SUM(aml.debit) AS debit, 
                        SUM(aml.credit) AS credit,
                        SUM(aml.balance) AS balance,
                    
                        aa.name AS account_name,
                        aaa.sale as sale,
                        aa.account_type as account_type,
                        aml.date as date,
                        aaa.name AS analytic_name,
                        aag.name AS group_name,
                        aaa.sale_profit,
                        am.compl_food_pric,
                        am.food_tast,
                        rc.name AS rc_name,
                        cbl.planned_amount,
                        cbl.date_from,
                        cbl.date_to,
                        et.event_type,
                        aat.name as type_name
                    
                    
                        FROM account_move_line AS aml
                        LEFT JOIN crossovered_budget_lines AS cbl ON aml.analytic_account_id = cbl.analytic_account_id AND aml.date BETWEEN cbl.date_from AND cbl.date_to 
                        LEFT JOIN crossovered_budget as cb on cbl.crossovered_budget_id = cb.id
                        LEFT JOIN account_move AS am ON am.id = aml.move_id
                        LEFT JOIN res_company rc ON aml.company_id = rc.id
                        LEFT JOIN account_account AS aa ON aa.id = aml.account_id
                        LEFT JOIN account_account_type as aat on aa.user_type_id = aat.id
                    
                        LEFT JOIN account_budget_post AS abp ON cbl.general_budget_id = abp.id
                        LEFT JOIN account_budget_rel AS abr ON abr.budget_id = abp.id 
                        LEFT JOIN account_analytic_account AS aaa ON cbl.analytic_account_id = aaa.id
                        LEFT JOIN account_analytic_group AS aag ON cbl.analytic_group = aag.id
                        LEFT JOIN event_type_sale AS et ON aml.event_type_id = et.id 
                    
                        WHERE 
                            aml.analytic_account_id IS NOT NULL 
                            AND aaa.sale_profit != 'management' 
                            AND aml.parent_state = 'posted'
                            AND aml.event_type_id = cbl.event_type
                            AND aml.account_id = abr.account_id
                            and aml.company_id in (%s) %s
                            and cb.state ='done'
                    
                    
                        GROUP BY 
                            aa.name,
                            aaa.sale,
                            aa.account_type,
                            aml.date,
                            aaa.name,
                            aag.name,
                            aaa.sale_profit,
                            am.compl_food_pric,
                            am.food_tast,
                            rc.name,
                            cbl.planned_amount,
                            cbl.date_from,
                            cbl.date_to,
                            et.event_type,
                            aat.name
                    
                        UNION
                    
                        SELECT 
                            sum(debit) AS debit,
                            sum(credit) AS credit,
                            sum(aml.balance) as balance,
                            aa.name AS account,
                            aaa.sale,
                            aa.account_type,
                            aml.date,
                            aaa.name AS analytic_name,
                            aag.name AS group_name,
                            NULL AS sale_profit,
                            NULL AS compl_food_pric,
                            NULL AS food_tast,
                            rc.name AS rc_name,
                            cbl.planned_amount,
                            cbl.date_from,
                            cbl.date_to,
                            NULL AS event_type,
                            aat.name as type_name
                    
                        FROM crossovered_budget_lines AS cbl
                        LEFT JOIN crossovered_budget AS cb ON cb.id = cbl.crossovered_budget_id
                        LEFT JOIN account_move_line AS aml on cbl.analytic_account_id = aml.analytic_account_id
                        LEFT JOIN res_company rc ON cb.company_id = rc.id
                        LEFT JOIN account_analytic_account AS aaa ON cbl.analytic_account_id = aaa.id
                        LEFT JOIN account_analytic_group AS aag ON cbl.analytic_group = aag.id
                        LEFT JOIN account_budget_post AS abp ON cbl.general_budget_id = abp.id
                        LEFT JOIN account_budget_rel AS abr ON abr.budget_id = abp.id 
                        LEFT JOIN account_account AS aa ON aa.id = abr.account_id
                        LEFT JOIN account_account_type as aat on aa.user_type_id = aat.id
                    
                        WHERE 
                            aaa.sale_profit != 'management' 
                            and cbl.event_type is null 
                            AND aml.date BETWEEN cbl.date_from AND cbl.date_to 
                            and aml.company_id in (%s) %s
                            and cb.state = 'done'
                    
                        GROUP BY 
                            aaa.name,
                            aag.name,
                            rc.name,
                            cbl.date_from,
                            cbl.date_to,
                            aa.name,
                            cbl.planned_amount,
                            cbl.event_type,
                            aa.account_type,
                            aml.date,
                            aaa.sale,
                            aat.name;
    
                    """ % (company_ids_str, condition, company_ids_str, condition)

            self._cr.execute(query)
            acnt_move_ids = self.env.cr.dictfetchall()

            if not acnt_move_ids:
                raise Warning(_("Nothing to print in this month"))

            product_querry = """SELECT
                                    sum(svl.remaining_value) as remaining_value,
                                    sum(svl.value) as total_value,
                                    rc.name,
                                    DATE(svl.create_date) as date
                                FROM
                                    stock_valuation_layer as svl
                                LEFT JOIN
                                    product_product as pp ON pp.id = svl.product_id
                                LEFT JOIN
                                    product_template as pt ON pt.id = pp.product_tmpl_id
                                LEFT JOIN
                                    res_company as rc on svl.company_id = rc.id
                                WHERE
                                    pt.type = 'product' and svl.remaining_value is not null and svl.company_id in (%s) %s
                                GROUP BY
                                    rc.name,
                                    DATE(svl.create_date)
                                ORDER BY 
                                    DATE(svl.create_date)""" % (company_ids_str, product_condition)

            self._cr.execute(product_querry)
            product_move_ids = self.env.cr.dictfetchall()

            stock_account_querry = """SELECT
                                        aml.date,aa.name,aa.code,sum(aml.debit) as debit
                                    FROM
                                        account_move_line as aml
                                    LEFT JOIN
                                        account_account as aa ON aml.account_id = aa.id
                                    WHERE
                                    aa.code = '110300' and aml.company_id in (%s) %s
                                    GROUP BY
                                        aml.date,aa.name,aa.code""" % (company_ids_str, condition)

            self._cr.execute(stock_account_querry)
            stock_move_ids = self.env.cr.dictfetchall()




            rows = []
            lens = []
            for i in acnt_move_ids:
                rows.append({
                    'rc_name': i['rc_name'],
                    'food_tast': i['food_tast'] if i['food_tast'] else 0,
                    'compl_food_pric': i['compl_food_pric'] if i['compl_food_pric'] else 0,
                    'analytic_account_name': i['analytic_name'],
                    'date': i['date'],
                    'planned_amount': i['planned_amount'],
                    'credit': i['credit'],
                    'debit': i['debit'],
                    'sale': i['sale'],
                    'balance': i['balance'],
                    'group_name': i['group_name'],
                    'event_type': i['event_type'],
                    'type_name': i['type_name'],
                    'account_type': i['account_type'],
                    'account': i['account_name'],
                })
                lens.append({
                    'data': {
                        'date': i['date'],

                    }
                })

            no_dup = []
            for p in lens:
                if p['data'] not in no_dup:
                    no_dup.append(p['data'])

            inv = []
            for v in no_dup:
                d_date = v['date']
                vals = []
                for i in rows:
                    if i['date'] == d_date:
                        vals.append({
                            'rc_name': i['rc_name'],
                            'food_tast': i['food_tast'],
                            'compl_food_pric': i['compl_food_pric'],
                            'analytic_account_name': i['analytic_account_name'],
                            'date': i['date'],
                            'planned_amount': i['planned_amount'],
                            'credit': i['credit'],
                            'debit': i['debit'],
                            'sale': i['sale'],
                            'balance': i['balance'],
                            'group_name': i['group_name'],
                            'event_type': i['event_type'],
                            'type_name': i['type_name'],
                            'account_type': i['account_type'],
                            'account': i['account'],

                        })
                inv.append({'date': d_date, 'vals': vals})



            data = {
                'from_date': self.from_date.strftime('%d-%m-%Y'),
                'to_date': self.to_date.strftime('%d-%m-%Y'),
                'result': inv,
                'product_result': product_move_ids,
                'stock_result': stock_move_ids
            }

            return {
                'type': 'ir.actions.report',
                'data': {
                    'model': 'profit.loss',
                    'options': json.dumps(data, default=date_utils.json_default),
                    'output_format': 'xlsx',
                    'report_name': 'Profit and Loss Report',
                },
                'report_type': 'xlsx'
            }

    def get_xlsx_report(self, data, response):
        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})
        sheet = workbook.add_worksheet('Customer Order')
        bold = workbook.add_format({'bold': True})
        bold_1 = workbook.add_format({'bold': True})

        format_1 = workbook.add_format(
            {'font_size': 13, 'bold': True, 'align': 'center', 'valign': 'vcenter', 'bg_color': '#BDB76B', 'border': 1})
        format_1.set_font_name('Times New Roman')

        format_3 = workbook.add_format(
            {'font_size': 30, 'bold': True, 'align': 'center', 'valign': 'center', 'bg_color': '#BDB76B', 'border': 1})

        format_4 = workbook.add_format(
            {'font_size': 13, 'bold': True, 'align': 'center', 'valign': 'center', 'bg_color': '#BDB76B', 'border': 1})

        format_6 = workbook.add_format(
            {'bold': True, 'align': 'left', 'valign': 'left', 'bg_color': '#FFFF00', 'font_size': 11, 'border': 1})


        sheet.set_column('D:D', 25)
        sheet.set_column('C:C', 25)
        sheet.set_column('E:E', 19)
        sheet.set_column('G:G', 20)
        sheet.set_column('F:F', 25)
        sheet.set_column('B:B', 25)
        sheet.set_column('K:K', 25)
        sheet.set_column('L:L', 25)
        sheet.set_column('M:M', 25)
        sheet.set_column('N:N', 25)
        sheet.set_column('O:O', 25)
        sheet.set_column('P:P', 25)
        sheet.set_column('Q:Q', 25)
        sheet.set_column('R:R', 25)
        sheet.set_column('S:S', 25)
        sheet.set_column('T:T', 25)
        sheet.set_column('U:U', 25)
        sheet.set_column('V:V', 25)
        sheet.set_column('W:W', 25)
        sheet.set_column('X:X', 25)
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

            months.append((current_year, month_name, col_index))
            month_columns.append({'month_name': month_name, 'col_index': col_index})

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
            sheet.merge_range(mgt_start + ':' + mgt_cell_end, f'P AND L REPORT {year}', format_3)
            sheet.merge_range('A8:A9', 'PARTICULARS', bold)
            sheet.merge_range(budgeted_cell_start + ':' + budgeted_cell_end, f'BUDGETED {month_name} {year}', bold_1)
            sheet.merge_range(actual_cell_start + ':' + actual_cell_end, f'ACTUAL {month_name} {year}', bold_1)

        cols = col_index + 1


        group_names = {}
        other_income = {}
        disc_vouch = {}
        group_names_accou = {}
        direct_expenses = {}



        for group_data in data['result']:
            if 'vals' in group_data:
                group_vals = group_data['vals']

                for item in group_vals:
                    item_date = datetime.strptime(group_data['date'], '%Y-%m-%d').date()

                    item_month = item_date.strftime('%B').upper()

                    if start_date <= item_date <= end_date:
                        group_name = 'REVENUE'
                        group_name_in = 'OTHER INCOME'

                        food_comp_name = 'FOOD / COMPLEMENTARY'
                        account_name = item['account']
                        planned_amount = item['planned_amount']
                        balance = item['balance']
                        event_type = item['event_type']
                        account_type = item['account_type']
                        group_exp = item['group_name']
                        food_tast = item['food_tast']
                        compl_food_pric = item['compl_food_pric']
                        account_type_name = item['type_name']

                        if item['sale'] and event_type is not None:
                            group_names.setdefault(group_name, {}).setdefault(event_type, {}).setdefault(item_month, {
                                'planned_amount': 0,'balance': 0,'food_tast': 0,'compl_food_pric': 0})

                            if item_month not in group_names[group_name][event_type]:
                                group_names[group_name][event_type][item_month] = {'planned_amount': 0, 'balance':0, 'food_tast': 0, 'compl_food_pric': 0}

                            group_names[group_name][event_type][item_month]['planned_amount'] = planned_amount
                            group_names[group_name][event_type][item_month]['balance'] += balance
                            group_names[group_name][event_type][item_month]['compl_food_pric'] += compl_food_pric
                            group_names[group_name][event_type][item_month]['food_tast'] += food_tast


                        if item['sale'] and event_type is None and account_type is None:
                            event_type = food_comp_name
                            group_names.setdefault(group_name, {}).setdefault(event_type, {}).setdefault(item_month, {
                            'planned_amount':0,'balance': 0})

                            if item_month not in group_names[group_name][event_type]:
                                group_names[group_name][event_type][item_month] = {'planned_amount': 0, 'balance': 0}
                            group_names[group_name][event_type][item_month]['planned_amount'] = planned_amount

                        if item['sale'] and account_type:
                            disc_vouch.setdefault(group_name, {}).setdefault(account_name, {}).setdefault(item_month,
                             {'planned_amount': 0,'balance': 0})

                            if item_month not in disc_vouch[group_name][account_name]:
                                disc_vouch[group_name][account_name][item_month] = {'planned_amount': 0, 'balance': 0}
                            disc_vouch[group_name][account_name][item_month]['planned_amount'] = planned_amount
                            disc_vouch[group_name][account_name][item_month]['balance'] += balance

                        if not item['sale'] and account_type_name == 'DIRECT EXPENSES':
                            direct_expenses.setdefault(account_type_name, {}).setdefault(account_name, {}).setdefault(item_month,
                            {'planned_amount': 0,'balance': 0})

                            direct_expenses[account_type_name][account_name][item_month]['planned_amount'] = planned_amount
                            direct_expenses[account_type_name][account_name][item_month]['balance'] += balance

                        if item['sale'] and account_type_name == 'Other Income':
                            other_income.setdefault(group_name_in, {}).setdefault(account_name, {}).setdefault(item_month,
                            {'planned_amount': 0,'balance': 0})

                            if item_month not in other_income[group_name_in][account_name]:
                                other_income[group_name_in][account_name][item_month] = {'planned_amount': 0, 'balance': 0}
                            other_income[group_name_in][account_name][item_month]['planned_amount'] = planned_amount
                            other_income[group_name_in][account_name][item_month]['balance'] += balance

                        if not item['sale'] and event_type is None and not account_type_name == 'DIRECT EXPENSES':
                            group_names_accou.setdefault(group_exp, {}).setdefault(account_name, {}).setdefault(item_month,
                            {'planned_amount': 0,'balance': 0})

                            group_names_accou[group_exp][account_name][item_month]['planned_amount'] = planned_amount
                            group_names_accou[group_exp][account_name][item_month]['balance'] += balance


        if group_names:
            for event_type in group_names[group_name]:
                if event_type != food_comp_name:
                    for item_month in group_names[group_name][event_type]:
                        food_comp_balance = 0

                        if item_month in group_names[group_name][event_type]:
                            food_comp_balance += (
                                    group_names[group_name][event_type][item_month]['compl_food_pric']
                                    + group_names[group_name][event_type][item_month]['food_tast']
                            )

                        group_names[group_name][food_comp_name][item_month]['balance'] += food_comp_balance

        if group_name and disc_vouch:
            group_names[group_name].update(disc_vouch[group_name])



        result_dict = {}
        open_result_dict = {}
        total_cost_per_month = {}



        for product_data in data['product_result']:
            if product_data:
                if 'date' in product_data:
                    date_str = product_data['date']

                    open_date = datetime.strptime(date_str, '%Y-%m-%d').date()

                    month = open_date.strftime('%B').upper()
                    last_day_of_month = open_date + relativedelta(day=31)
                    opening_date = start_date - timedelta(days=1)

                    if last_day_of_month.month != open_date.month:
                        last_day_of_month -= relativedelta(months=1)

                    month_names = last_day_of_month.strftime('%B').upper()
                    open_month_names = opening_date.strftime('%B').upper()

                    result_dict[month_names] = product_data['remaining_value']
                    open_result_dict[open_month_names] = product_data['remaining_value']

                    if month in total_cost_per_month:
                        total_cost_per_month[month] += product_data['total_value']
                    else:
                        total_cost_per_month[month] = product_data['total_value']

        stock_dict = {}


        for stock_data in data['stock_result']:
            if stock_data:
                if 'date' in stock_data:
                    debit_amount = stock_data['debit']
                    date_str_stk = stock_data['date']
                    open_date = datetime.strptime(date_str_stk, '%Y-%m-%d').date()
                    month_name_stk = open_date.strftime('%B').upper()

                    if month_name_stk not in stock_dict:
                        stock_dict[month_name_stk] = {'debit':0}
                    stock_dict[month_name_stk]['debit'] += debit_amount


        # REVENUE  FROM EACH COMPANY

        row = 9
        col = 0
        month_list = []
        group_total_planned_amount_sales = 0
        group_total_balance_sales = 0

        for group_name, items_sales in group_names.items():
            sheet.write(row, col, group_name, format_4)
            for col_index_2 in range(1, cols + 1):
                sheet.write(row, col + col_index_2, None, format_4)
            row += 1

            for event_type, item_sales_group in items_sales.items():
                sheet.write(row, col, event_type, bold)

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

        dir_row = row



        group_total_planned_amount_dir_exp = 0
        group_total_balance_dir_exp = 0
        month_list_exp = []

        for account_type_name, direct_items in direct_expenses.items():
            sheet.write(row, col, account_type_name, format_4)
            for col_index_2 in range(1, cols + 1):
                sheet.write(row, col + col_index_2, None, format_4)
            row += 1
            for account_name, item_accou_direct_group in direct_items.items():
                sheet.write(row, col, account_name, bold)

                for month_index in range(1, 13):
                    month_name = calendar.month_name[month_index].upper()
                    col_index = None

                    for month_dict in month_columns:
                        if month_dict['month_name'] == month_name:
                            col_index = month_dict['col_index']
                            break

                    if month_name in item_accou_direct_group:
                        item_group = item_accou_direct_group[month_name]
                        dir_exp_planned = item_group['planned_amount']
                        dir_exp_balance = item_group['balance']

                        sheet.write(row, col + col_index, dir_exp_planned, bold)
                        sheet.write(row, col + col_index + 1, dir_exp_balance, bold)

                        group_total_planned_amount_dir_exp += dir_exp_planned
                        group_total_balance_dir_exp += dir_exp_balance

                        month_list_exp.append({
                            'col_index': col_index,
                            'exp_planned_other': dir_exp_planned,
                            'exp_balance_other': dir_exp_balance,
                        })

                row += 1

        sum_dir_planned = {}
        sum_dir_balance = {}

        for item_dir in month_list_exp:
            col_index = item_dir['col_index']
            if col_index not in sum_dir_planned:
                sum_dir_planned[col_index] = 0
            if col_index not in sum_dir_balance:
                sum_dir_balance[col_index] = 0

            sum_dir_planned[col_index] += item_dir['exp_planned_other']
            sum_dir_balance[col_index] += item_dir['exp_balance_other']


        sheet.write(row, col, 'CLOSING INVENTORY', format_6)
        sheet.write(dir_row + 1, col, 'OPENING INVENTORY', bold)

        for open_month_names, open_value in open_result_dict.items():
            sheet.write(dir_row + 1, col + col_index, 0, bold)
            sheet.write(dir_row + 1, col + col_index + 1, open_value, bold)


        for month_names, value in result_dict.items():
            col_index = None
            for month_dict in month_columns:
                if month_dict['month_name'] == month_names:
                    col_index = month_dict['col_index']
                    break

            sheet.write(row, col + col_index, None, format_6)


            sheet.write(row, col + col_index + 1, value, format_6)

        row += 1


        sheet.write(row, col, 'COST OF GOODS SOLD', format_6)

        for month_name_stk,stock_val in stock_dict.items():
            debit = stock_val['debit']
            col_index = None
            for month_dict in month_columns:
                if month_dict['month_name'] == month_name_stk:
                    col_index = month_dict['col_index']
                    break

            sheet.write(row, col + col_index, None, format_6)
            sheet.write(row, col + col_index + 1, debit, format_6)

        row+=1

        sheet.write(row, col, 'NET PROFIT FROM CATERING', format_6)
        sheet.write(row +1, col, 'NET PROFIT FROM CATERING % ', format_6)

        for col_index in sum_dir_balance:
            total = sum_dir_balance[col_index]


            if col_index in sum_sales_balance:
                total_other = sum_sales_balance[col_index]
                cat_revenu = total - total_other
                cat_rev_percentage = (cat_revenu / total_other) * 100
                sheet.write(row, col_index, None, format_6)
                sheet.write(row, col_index + 1, cat_revenu, format_6)
                row+=1

                sheet.write(row, col_index, None, format_6)
                sheet.write(row, col_index + 1, round(cat_rev_percentage,2), format_6)

        row +=1

        food_row = row

        row += 1
        #
        # OTHER INCOME  FROM ANOTHER LOCATION

        month_list_other = []
        group_total_planned_amount_other = 0
        group_total_balance_other = 0

        for group_name_in, other_income_items in other_income.items():
            sheet.write(row, col, group_name_in, format_4)
            for col_index_2 in range(1, cols + 1):
                sheet.write(row, col + col_index_2, None, format_4)
            row += 1

            for account_name, other_income_items_data in other_income_items.items():
                sheet.write(row, col, account_name, bold)

                for month_index in range(1, 13):
                    month_name = calendar.month_name[month_index].upper()
                    col_index = None

                    for month_dict in month_columns:
                        if month_dict['month_name'] == month_name:
                            col_index = month_dict['col_index']
                            break

                    if month_name in other_income_items_data:
                        item_group = other_income_items_data[month_name]
                        sales_planned_other = item_group['planned_amount']
                        sales_balance_other = item_group['balance']
                        sheet.write(row, col + col_index, sales_planned_other, bold)
                        sheet.write(row, col + col_index + 1, sales_balance_other, bold)
                        group_total_planned_amount_other += sales_planned_other
                        group_total_balance_other += sales_balance_other

                        month_list_other.append({
                            'col_index': col_index,
                            'sales_planned_other': sales_planned_other,
                            'sales_balance_other': sales_balance_other,
                        })

                row += 1

        sum_other_planned = {}
        sum_other_balance = {}

        for item in month_list_other:
            col_index = item['col_index']
            if col_index not in sum_other_planned:
                sum_other_planned[col_index] = 0
            if col_index not in sum_other_balance:
                sum_other_balance[col_index] = 0

            sum_other_planned[col_index] += item['sales_planned_other']
            sum_other_balance[col_index] += item['sales_balance_other']

        for col_index in sum_other_planned:
            sheet.write(row, col, f'TOTAL OF {group_name}', bold)
            sheet.write(row, col_index, sum_other_planned[col_index], bold)
            sheet.write(row, col_index + 1, sum_other_balance[col_index], bold)

        row += 1

        sheet.write(row, col, 'GROSS REVENUE', format_6)
        sheet.write(row + 1, col, 'GROSS PROFIT', format_6)
        sheet.write(row + 2, col, 'GROSS PROFIT %', format_6)

        for col_index in sum_sales_balance:
            other_inc_total = sum_sales_balance[col_index]
            if sum_other_balance:
                if col_index in sum_other_balance:
                    revenue_total = sum_other_balance[col_index]
                    total_inc = other_inc_total + revenue_total
                    sheet.write(row, col_index, None, format_6)

                    sheet.write(row, col_index + 1, total_inc, format_6)
                    if col_index in sum_dir_balance:
                        dir_tootal = sum_dir_balance[col_index]
                        gross_pr = total_inc - dir_tootal
                        gross_pr_per = (gross_pr / total_inc) * 100
                        sheet.write(row + 1, col_index, None, format_6)
                        sheet.write(row + 2, col_index,None, format_6)
                        sheet.write(row + 1, col_index + 1, gross_pr, format_6)
                        sheet.write(row + 2, col_index + 1, round(gross_pr_per,2), format_6)

        row += 3

        sheet.write(food_row, col, 'FOOD COST', format_6)

        for col_index in sum_sales_balance:
            other_inc_total = sum_sales_balance[col_index]
            if sum_other_balance:
                if col_index in sum_other_balance:
                    revenue_total = sum_other_balance[col_index]
                    total_inc = other_inc_total + revenue_total
                    for month, month_value in total_cost_per_month.items():
                        col_index_2 = None
                        for month_dict in month_columns:
                            if month_dict['month_name'] == month:
                                col_index_2 = month_dict['col_index']
                                break

                        if col_index_2 == col_index:
                            food_cost_perc = (month_value / total_inc) * 100
                            print(food_cost_perc)
                            sheet.write(food_row, col_index_2,None,format_6)

                            sheet.write(food_row, col_index_2 + 1, round(food_cost_perc,2),format_6)
            else:
                pass


        # OTHER EXPENSES FROM COMPANY

        group_total_planned_amount_exp = 0
        group_total_balance_exp = 0


        account_total = {}

        for group_exp, items_accou in group_names_accou.items():
            sheet.write(row, col, group_exp, format_4)
            for col_index_2 in range(1, cols + 1):
                sheet.write(row, col + col_index_2, None, format_4)
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
                sheet.write(row, col, f'TOTAL OF {group_exp}', bold)
                sheet.write(row, col_index, sum_exp_planned[col_index], bold)
                sheet.write(row, col_index + 1, sum_exp_balance[col_index], bold)
            row += 1

            for col_index, items in sum_exp_balance.items():

                if col_index not in account_total:
                    account_total[col_index] = 0
                account_total[col_index] += sum_exp_balance[col_index]




            sheet.write(row, col,'TOTAL OF EXPENSES', format_6)
            sheet.write(row + 1, col,'NET PROFIT', format_6)
            sheet.write(row + 2, col,'NET PROFIT %', format_6)

            for col_index in account_total:
                total_exp = account_total[col_index]
                if col_index in sum_dir_balance:
                    total_dir = sum_dir_balance[col_index]
                    tot_exp_all = total_dir + total_exp
                    sheet.write(row, col_index,None, format_6)
                    sheet.write(row, col_index + 1,tot_exp_all, format_6)

                    for col_index in sum_sales_balance:
                        other_inc_total = sum_sales_balance[col_index]
                        if sum_other_balance:
                            if col_index in sum_other_balance:
                                revenue_total = sum_other_balance[col_index]
                                total_inc = other_inc_total + revenue_total
                                sheet.write(row + 1, col_index, None, format_6)
                                sheet.write(row + 1, col_index + 1, total_inc, format_6)

                                net_proit = total_inc - tot_exp_all
                                bet_proit_per = (net_proit / total_inc) * 100


                                sheet.write(row, col_index + 1, net_proit, format_6)
                                sheet.write(row + 2, col_index, None, format_6)
                                sheet.write(row + 2, col_index + 1, round(bet_proit_per,2), format_6)

        workbook.close()
        output.seek(0)
        response.stream.write(output.read())
        output.close()
