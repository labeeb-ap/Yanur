import io

from odoo import models, fields, _
from datetime import date
from odoo.http import request
from odoo.tools import date_utils
from odoo.tools.safe_eval import json
from odoo.exceptions import Warning

try:
    from odoo.tools.misc import xlsxwriter
except ImportError:
    import xlsxwriter


class BalanceSheetReportWizard(models.TransientModel):
    _name = 'balance.sheet.report.wizard'
    _description = 'Balance Sheet Report'

    start_date = fields.Date(string='Start Date', default=date.today())
    end_date = fields.Date(string='End Date', default=date.today())
    company_ids = fields.Many2many('res.company', string="Company")
    detailed_summary = fields.Boolean(string="Detailed Summary", store=True)

    def print_pdf_report(self):
        if self.start_date > self.end_date:
            raise Warning(_("Start Date is GreaterThan End Date"))
        else:
            filter_cdtn1 = '''where am.state = 'posted' and aat.internal_group in ('income', 'expense') and
                 aml.date between '%s' AND '%s'
                 ''' % (self.start_date, self.end_date)
            filter_cdtn2 = '''where am.state = 'posted' and aat.internal_group in ('asset', 'liability') and
                             aml.date between '%s' AND '%s'
                             ''' % (self.start_date, self.end_date)
        if self.company_ids:
            if len(self.company_ids) == 1:
                filter_cdtn1 += '''and aml.company_id = '%s'
                ''' % (self.company_ids.ids[0])
                filter_cdtn2 += '''and aml.company_id = '%s'
                ''' % (self.company_ids.ids[0])
            else:
                filter_cdtn1 += '''and aml.company_id in {}
                '''.format(tuple(self.company_ids.ids))
                filter_cdtn2 += '''and aml.company_id in {}
                '''.format(tuple(self.company_ids.ids))

        query1 = """select aml.date date, aa.id account_id, aml.debit debit, aml.credit credit, 
                    aat.internal_group account_type, aml.company_id company from account_move_line aml
                    left join account_move am on aml.move_id = am.id
                    left join account_account aa on aml.account_id = aa.id
                    left join account_account_type aat on aa.user_type_id = aat.id %s""" % (
            filter_cdtn1)

        query2 = """select aml.date date, aa.id account_id, aa.code account_code, aa.name account_name, aml.debit debit, aml.credit credit, 
                    aat.id account_type_id, aat.name account_type_name, aat.internal_group account_type, 
                    aml.company_id company, aat.type_order account_type_order from account_move_line aml
                    left join account_move am on aml.move_id = am.id
                    left join account_account aa on aml.account_id = aa.id
                    left join account_account_type aat on aa.user_type_id = aat.id %s""" % (
            filter_cdtn2)

        self._cr.execute(query1)
        profit_loss_ids = self._cr.dictfetchall()

        self._cr.execute(query2)
        balance_sheet_ids = self._cr.dictfetchall()

        rows1 = []
        accounts1 = []

        for i in profit_loss_ids:
            rows1.append({
                'acc_id': i['account_id'],
                'acc_debit': i['debit'],
                'acc_credit': i['credit'],
                'acc_type': i['account_type'],
            })
            accounts1.append({'data': {
                'acc_id': i['account_id'],
            }})

        no_dup_account1 = []
        for j in accounts1:
            if j['data'] not in no_dup_account1:
                no_dup_account1.append(j['data'])

        inv1 = []
        for k in no_dup_account1:
            chart_acc_id = k['acc_id']
            line_debit = 0
            line_credit = 0
            chart_type = ''

            for l in rows1:
                if l['acc_id'] == chart_acc_id:
                    line_debit += l['acc_debit']
                    line_credit += l['acc_credit']
                    chart_type = l['acc_type']

            inv1.append({
                'acc_id': chart_acc_id,
                'acc_debit': line_debit,
                'acc_credit': line_credit,
                'acc_type': chart_type,
            })

        rows2 = []
        accounts2 = []
        lens2 = []

        for w in balance_sheet_ids:
            rows2.append({
                'acc_id': w['account_id'],
                'acc_code': w['account_code'],
                'acc_name': w['account_name'],
                'acc_debit': w['debit'],
                'acc_credit': w['credit'],
                'acc_type_id': w['account_type_id'],
                'acc_type_name': w['account_type_name'],
                'acc_type': w['account_type'],
            })
            accounts2.append({'data': {
                'acc_id': w['account_id'],
            }})
            lens2.append({
                'acc_type_id': w['account_type_id'],
                'acc_type_name': w['account_type_name'],
                'acc_type': w['account_type'],
                'acc_type_order': w['account_type_order'],
            })

        no_dup_lens2 = []
        for x in lens2:
            if x not in no_dup_lens2:
                no_dup_lens2.append(x)

        no_dup_lens2.sort(key=lambda q: q['acc_type_order'])

        no_dup_account2 = []
        for y in accounts2:
            if y['data'] not in no_dup_account2:
                no_dup_account2.append(y['data'])

        inv2 = []
        for z in no_dup_account2:
            chart_acc_id = z['acc_id']
            chart_acc_code = ''
            chart_acc_name = ''
            line_debit = 0
            line_credit = 0
            chart_type_id = ''
            chart_type_name = ''
            chart_type = ''

            for r in rows2:
                if r['acc_id'] == chart_acc_id:
                    chart_acc_code = r['acc_code']
                    chart_acc_name = r['acc_name']
                    line_debit += r['acc_debit']
                    line_credit += r['acc_credit']
                    chart_type_id = r['acc_type_id']
                    chart_type_name = r['acc_type_name']
                    chart_type = r['acc_type']

            inv2.append({
                'acc_id': chart_acc_id,
                'acc_code': chart_acc_code,
                'acc_name': chart_acc_name,
                'acc_debit': line_debit,
                'acc_credit': line_credit,
                'acc_type_id': chart_type_id,
                'acc_type_name': chart_type_name,
                'acc_type': chart_type,
            })

        data = {
            'ids': self.ids,
            'model': self._name,
            'net': inv1,
            'vals': inv2,
            'type': no_dup_lens2,
            'summary': self.detailed_summary,
            'start': self.start_date.strftime("%d-%b-%Y"),
            'end': self.end_date.strftime("%d-%b-%Y"),
        }
        action = self.env.ref('bs_pl_report.balance_sheet_report_pdf').report_action(self, data=data)
        # action.update({'close_on_report_download': True})
        return action

    def print_xl_report(self):
        if self.start_date > self.end_date:
            raise Warning(_("Start Date is GreaterThan End Date"))
        else:
            filter_cdtn1 = '''where am.state = 'posted' and aat.internal_group in ('income', 'expense') and
                 aml.date between '%s' AND '%s'
                 ''' % (self.start_date, self.end_date)
            filter_cdtn2 = '''where am.state = 'posted' and aat.internal_group in ('asset', 'liability') and
                             aml.date between '%s' AND '%s'
                             ''' % (self.start_date, self.end_date)
        if self.company_ids:
            if len(self.company_ids) == 1:
                filter_cdtn1 += '''and aml.company_id = '%s'
                ''' % (self.company_ids.ids[0])
                filter_cdtn2 += '''and aml.company_id = '%s'
                ''' % (self.company_ids.ids[0])
            else:
                filter_cdtn1 += '''and aml.company_id in {}
                '''.format(tuple(self.company_ids.ids))
                filter_cdtn2 += '''and aml.company_id in {}
                '''.format(tuple(self.company_ids.ids))

        query1 = """select aml.date date, aa.id account_id, aml.debit debit, aml.credit credit, 
                    aat.internal_group account_type, aml.company_id company from account_move_line aml
                    left join account_move am on aml.move_id = am.id
                    left join account_account aa on aml.account_id = aa.id
                    left join account_account_type aat on aa.user_type_id = aat.id %s""" % (
            filter_cdtn1)

        query2 = """select aml.date date, aa.id account_id, aa.code account_code, aa.name account_name, aml.debit debit, aml.credit credit, 
                    aat.id account_type_id, aat.name account_type_name, aat.internal_group account_type, 
                    aml.company_id company, aat.type_order account_type_order from account_move_line aml
                    left join account_move am on aml.move_id = am.id
                    left join account_account aa on aml.account_id = aa.id
                    left join account_account_type aat on aa.user_type_id = aat.id %s""" % (
            filter_cdtn2)

        self._cr.execute(query1)
        profit_loss_ids = self._cr.dictfetchall()

        self._cr.execute(query2)
        balance_sheet_ids = self._cr.dictfetchall()

        rows1 = []
        accounts1 = []

        for i in profit_loss_ids:
            rows1.append({
                'acc_id': i['account_id'],
                'acc_debit': i['debit'],
                'acc_credit': i['credit'],
                'acc_type': i['account_type'],
            })
            accounts1.append({'data': {
                'acc_id': i['account_id'],
            }})

        no_dup_account1 = []
        for j in accounts1:
            if j['data'] not in no_dup_account1:
                no_dup_account1.append(j['data'])

        inv1 = []
        for k in no_dup_account1:
            chart_acc_id = k['acc_id']
            line_debit = 0
            line_credit = 0
            chart_type = ''

            for l in rows1:
                if l['acc_id'] == chart_acc_id:
                    line_debit += l['acc_debit']
                    line_credit += l['acc_credit']
                    chart_type = l['acc_type']

            inv1.append({
                'acc_id': chart_acc_id,
                'acc_debit': line_debit,
                'acc_credit': line_credit,
                'acc_type': chart_type,
            })

        rows2 = []
        accounts2 = []
        lens2 = []

        for w in balance_sheet_ids:
            rows2.append({
                'acc_id': w['account_id'],
                'acc_code': w['account_code'],
                'acc_name': w['account_name'],
                'acc_debit': w['debit'],
                'acc_credit': w['credit'],
                'acc_type_id': w['account_type_id'],
                'acc_type_name': w['account_type_name'],
                'acc_type': w['account_type'],
            })
            accounts2.append({'data': {
                'acc_id': w['account_id'],
            }})
            lens2.append({
                'acc_type_id': w['account_type_id'],
                'acc_type_name': w['account_type_name'],
                'acc_type': w['account_type'],
                'acc_type_order': w['account_type_order'],
            })

        no_dup_lens2 = []
        for x in lens2:
            if x not in no_dup_lens2:
                no_dup_lens2.append(x)

        no_dup_lens2.sort(key=lambda q: q['acc_type_order'])

        no_dup_account2 = []
        for y in accounts2:
            if y['data'] not in no_dup_account2:
                no_dup_account2.append(y['data'])

        inv2 = []
        for z in no_dup_account2:
            chart_acc_id = z['acc_id']
            chart_acc_code = ''
            chart_acc_name = ''
            line_debit = 0
            line_credit = 0
            chart_type_id = ''
            chart_type_name = ''
            chart_type = ''

            for r in rows2:
                if r['acc_id'] == chart_acc_id:
                    chart_acc_code = r['acc_code']
                    chart_acc_name = r['acc_name']
                    line_debit += r['acc_debit']
                    line_credit += r['acc_credit']
                    chart_type_id = r['acc_type_id']
                    chart_type_name = r['acc_type_name']
                    chart_type = r['acc_type']

            inv2.append({
                'acc_id': chart_acc_id,
                'acc_code': chart_acc_code,
                'acc_name': chart_acc_name,
                'acc_debit': line_debit,
                'acc_credit': line_credit,
                'acc_type_id': chart_type_id,
                'acc_type_name': chart_type_name,
                'acc_type': chart_type,
            })

        data = {
            'ids': self.ids,
            'model': self._name,
            'net': inv1,
            'vals': inv2,
            'type': no_dup_lens2,
            'summary': self.detailed_summary,
            'start': self.start_date.strftime("%d-%b-%Y"),
            'end': self.end_date.strftime("%d-%b-%Y"),

            'user_name': self.env.user.name,
            'current_date': fields.Datetime.context_timestamp(self, fields.Datetime.now()).strftime('%d/%m/%Y %H:%M'),

            'company_name': self.env.company.name,
            'com_street': self.env.company.street,
            'com_street2': self.env.company.street2,
            'com_city': self.env.company.city,
            'com_state': self.env.company.state_id.name,
            'com_zip': self.env.company.zip,
            'com_country': self.env.company.country_id.name,
            'com_phone': self.env.company.phone,
            'com_email': self.env.company.email,
        }
        return {
            'type': 'ir.actions.report',
            'data': {'model': 'balance.sheet.report.wizard',
                     'options': json.dumps(data, default=date_utils.json_default),
                     'output_format': 'xlsx',
                     'report_name': 'Balance Sheet Report',
                     },
            'report_type': 'xlsx',
        }

    def get_xlsx_report(self, data, response):
        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})

        row = 6
        col = 0
        sheet = workbook.add_worksheet('Balance Sheet')
        print_heading = workbook.add_format(
            {'bold': True, 'align': 'center', 'valign': 'vcenter', 'font_size': 15, 'bg_color': '#E8E8E8', 'border': 1})
        table_head1 = workbook.add_format(
            {'bold': True, 'align': 'center', 'valign': 'vcenter', 'font_size': 15, 'border': 1})
        table_head2 = workbook.add_format(
            {'bold': True, 'align': 'center', 'valign': 'vcenter', 'font_size': 15, 'bg_color': '#E8E8E8', 'border': 1})
        table_amount_td = workbook.add_format(
            {'bold': True, 'align': 'right', 'valign': 'vcenter', 'bg_color': '#E8E8E8', 'border': 1})
        type_amount_column = workbook.add_format(
            {'bold': True, 'align': 'right', 'valign': 'vcenter', 'bg_color': '#E8E8E8', 'border': 1,
             'color': '#C22806'})
        type_name_column = workbook.add_format(
            {'bold': True, 'valign': 'vcenter', 'border': 1, 'color': '#C22806'})
        value_column = workbook.add_format({'valign': 'vcenter', 'border': 1})
        com_address = workbook.add_format({'valign': 'vcenter', 'align': 'center', 'font_size': 14, 'border': 1})
        foot = workbook.add_format({'align': 'center', 'valign': 'vcenter', 'font_size': 10})

        sheet.write(row - 1, col + 1, 'Liability', table_head1)
        sheet.write(row - 1, col + 2, 'Amount', table_head2)
        sheet.write(row - 1, col + 3, 'Asset', table_head1)
        sheet.write(row - 1, col + 4, 'Amount', table_head2)

        sheet.merge_range('B2:E2',
                          str(data['company_name']) + '\n' + str(data['com_street']) + '\n' + str(
                              data['com_street2']) + '\n' + str(data[
                                                                    'com_city']) + ' ' + str(
                              data['com_state']) + ' ' + str(
                              data['com_zip']) + '\n' + str(
                              data['com_country']) + '\n' +
                          str(data['com_phone']) + '\n' + str(data['com_email']), com_address)
        sheet.merge_range('B3:E3', 'Balance Sheet', print_heading)
        sheet.merge_range('B4:E4', data['start'] + ' - ' + data['end'], print_heading)
        sheet.merge_range('B5:E5', '')

        row1 = 6
        for i in data['type']:
            if i['acc_type'] == 'liability':
                line_expense_sum = 0
                for j in data['vals']:
                    if j['acc_type_id'] == i['acc_type_id'] and j['acc_type'] == i['acc_type']:
                        line_expense_sum += (j['acc_credit'] - j['acc_debit'])
                sheet.write(row1, col + 1, ' ' + i['acc_type_name'], type_name_column)
                sheet.write(row1, col + 2, '%.2f' % line_expense_sum, type_amount_column)
                a = row1 + 1
                if data['summary'] == True:
                    for k in data['vals']:
                        if k['acc_type_id'] == i['acc_type_id'] and k['acc_type'] == i['acc_type']:
                            sheet.write(a, col + 1, '  ' + k['acc_code'] + ' ' + k['acc_name'], value_column)
                            sheet.write(a, col + 2, '%.2f' % (k['acc_credit'] - k['acc_debit']), table_amount_td)
                            a += 1
                row1 = a

        expense_total = 0
        for exp_tot in data['vals']:
            if exp_tot['acc_type'] == 'liability':
                expense_total += (exp_tot['acc_credit'] - exp_tot['acc_debit'])

        sheet.write(row1, col + 1, 'Total', table_head1)
        sheet.write(row1, col + 2, '%.2f' % expense_total, type_amount_column)

        net_value_liability1_income = 0
        net_value_liability1_expense = 0
        for net_lia_tot in data['net']:
            if net_lia_tot['acc_type'] == 'expense':
                net_value_liability1_expense += net_lia_tot['acc_debit'] - net_lia_tot['acc_credit']
            if net_lia_tot['acc_type'] == 'income':
                net_value_liability1_income += net_lia_tot['acc_credit'] - net_lia_tot['acc_debit']
        net_profit_liability = net_value_liability1_income - net_value_liability1_expense

        lia_l = row1
        if net_profit_liability > 0:
            sheet.write(lia_l + 1, col + 1, 'Net Profit', table_head1)
            sheet.write(lia_l + 1, col + 2, '%.2f' % net_profit_liability, type_amount_column)
            lia_l += 1

        row2 = 6
        for x in data['type']:
            if x['acc_type'] == 'asset':
                line_income_sum = 0
                for y in data['vals']:
                    if y['acc_type_id'] == x['acc_type_id'] and y['acc_type'] == x['acc_type']:
                        line_income_sum += (y['acc_debit'] - y['acc_credit'])
                sheet.write(row2, col + 3, ' ' + x['acc_type_name'], type_name_column)
                sheet.write(row2, col + 4, '%.2f' % line_income_sum, type_amount_column)
                b = row2 + 1
                if data['summary'] == True:
                    for z in data['vals']:
                        if z['acc_type_id'] == x['acc_type_id'] and z['acc_type'] == x['acc_type']:
                            sheet.write(b, col + 3, '  ' + z['acc_code'] + ' ' + z['acc_name'], value_column)
                            sheet.write(b, col + 4, '%.2f' % (z['acc_debit'] - z['acc_credit']), table_amount_td)
                            b += 1
                row2 = b

        income_total = 0
        for in_tot in data['vals']:
            if in_tot['acc_type'] == 'asset':
                income_total += (in_tot['acc_debit'] - in_tot['acc_credit'])
        sheet.write(row2, col + 3, 'Total', table_head1)
        sheet.write(row2, col + 4, '%.2f' % income_total, type_amount_column)

        as_l = row2
        if net_profit_liability < 0:
            sheet.write(as_l + 1, col + 3, 'Net Profit', table_head1)
            sheet.write(as_l + 1, col + 4, '%.2f' % net_profit_liability, type_amount_column)
            as_l += 1

        if lia_l >= row2:
            current_print = 'B' + str(lia_l + 2) + ':' + 'E' + str(lia_l + 2)
            sheet.set_row(lia_l + 1, 20)
            sheet.merge_range(current_print, data['user_name'] + ' ' + '-' + ' ' + data['current_date'], foot)
        else:
            current_print = 'B' + str(as_l + 2) + ':' + 'E' + str(as_l + 2)
            sheet.set_row(as_l + 1, 20)
            sheet.merge_range(current_print, data['user_name'] + ' ' + '-' + ' ' + data['current_date'], foot)

        sheet.set_column('B:B', 50)
        sheet.set_column('C:C', 20)
        sheet.set_column('D:D', 50)
        sheet.set_column('E:E', 20)

        sheet.set_row(1, 125)
        sheet.set_row(2, 35)
        sheet.set_row(3, 35)
        sheet.set_row(5, 35)

        workbook.close()
        output.seek(0)
        response.stream.write(output.read())
        output.close()
