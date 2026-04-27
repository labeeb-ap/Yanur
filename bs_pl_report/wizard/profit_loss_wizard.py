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


class ProfitLossReportWizard(models.TransientModel):
    _name = 'profit.loss.report.wizard'
    _description = 'Profit & Loss Report'

    start_date = fields.Date(string='Start Date', default=date.today())
    end_date = fields.Date(string='End Date', default=date.today())
    company_ids = fields.Many2many('res.company', string="Company")
    detailed_summary = fields.Boolean(string="Detailed Summary", store=True)

    def print_pdf_report(self):
        if self.start_date > self.end_date:
            raise Warning(_("Start Date is GreaterThan End Date"))
        else:
            filter_cdtn = '''where am.state = 'posted' and aat.internal_group in ('income', 'expense') and
                 aml.date between '%s' AND '%s'
                 ''' % (self.start_date, self.end_date)
        if self.company_ids:
            if len(self.company_ids) == 1:
                filter_cdtn += '''and aml.company_id = '%s'
                ''' % (self.company_ids.ids[0])
            else:
                filter_cdtn += '''and aml.company_id in {}
                '''.format(tuple(self.company_ids.ids))

        query = """select aml.date date, aa.id account_id, aa.code account_code, aa.name account_name, aml.debit debit, aml.credit credit, 
                    aat.id account_type_id, aat.name account_type_name, aat.internal_group account_type, aat.report_group account_type_report, 
                    aml.company_id company, aat.type_order account_type_order from account_move_line aml
                    left join account_move am on aml.move_id = am.id
                    left join account_account aa on aml.account_id = aa.id
                    left join account_account_type aat on aa.user_type_id = aat.id %s""" % (
            filter_cdtn)

        self._cr.execute(query)
        profit_loss_ids = self._cr.dictfetchall()

        rows = []
        accounts = []
        lens = []

        for i in profit_loss_ids:
            rows.append({
                'acc_id': i['account_id'],
                'acc_code': i['account_code'],
                'acc_name': i['account_name'],
                'acc_debit': i['debit'],
                'acc_credit': i['credit'],
                'acc_type_id': i['account_type_id'],
                'acc_type_name': i['account_type_name'],
                'acc_type': i['account_type'],
                'acc_type_report': i['account_type_report'],
            })
            accounts.append({'data': {
                'acc_id': i['account_id'],
            }})
            lens.append({
                'acc_type_id': i['account_type_id'],
                'acc_type_name': i['account_type_name'],
                'acc_type': i['account_type'],
                'acc_type_report': i['account_type_report'],
                'acc_type_order': i['account_type_order'],
            })

        no_dup_lens = []
        for j in lens:
            if j not in no_dup_lens:
                no_dup_lens.append(j)

        no_dup_lens.sort(key=lambda z: z['acc_type_order'])

        no_dup_account = []
        for a in accounts:
            if a['data'] not in no_dup_account:
                no_dup_account.append(a['data'])

        inv = []
        for b in no_dup_account:
            chart_acc_id = b['acc_id']
            chart_acc_code = ''
            chart_acc_name = ''
            line_debit = 0
            line_credit = 0
            chart_type_id = ''
            chart_type_name = ''
            chart_type = ''
            chart_type_report = ''

            for c in rows:
                if c['acc_id'] == chart_acc_id:
                    chart_acc_code = c['acc_code']
                    chart_acc_name = c['acc_name']
                    line_debit += c['acc_debit']
                    line_credit += c['acc_credit']
                    chart_type_id = c['acc_type_id']
                    chart_type_name = c['acc_type_name']
                    chart_type = c['acc_type']
                    chart_type_report = c['acc_type_report']

            inv.append({
                'acc_id': chart_acc_id,
                'acc_code': chart_acc_code,
                'acc_name': chart_acc_name,
                'acc_debit': line_debit,
                'acc_credit': line_credit,
                'acc_type_id': chart_type_id,
                'acc_type_name': chart_type_name,
                'acc_type': chart_type,
                'acc_type_report': chart_type_report,
            })
        data = {
            'ids': self.ids,
            'model': self._name,
            'vals': inv,
            'type': no_dup_lens,
            'summary': self.detailed_summary,
            'start': self.start_date.strftime("%d-%b-%Y"),
            'end': self.end_date.strftime("%d-%b-%Y"),
        }
        action = self.env.ref('bs_pl_report.profit_loss_report_pdf').report_action(self, data=data)
        # action.update({'close_on_report_download': True})
        return action

    def print_xl_report(self):
        if self.start_date > self.end_date:
            raise Warning(_("Start Date is GreaterThan End Date"))
        else:
            filter_cdtn = '''where am.state = 'posted' and aat.internal_group in ('income', 'expense') and
                 aml.date between '%s' AND '%s'
                 ''' % (self.start_date, self.end_date)
        if self.company_ids:
            if len(self.company_ids) == 1:
                filter_cdtn += '''and aml.company_id = '%s'
                ''' % (self.company_ids.ids[0])
            else:
                filter_cdtn += '''and aml.company_id in {}
                '''.format(tuple(self.company_ids.ids))

        query = """select aml.date date, aa.id account_id, aa.code account_code, aa.name account_name, aml.debit debit, aml.credit credit, 
                    aat.id account_type_id, aat.name account_type_name, aat.internal_group account_type, aat.report_group account_type_report, 
                    aml.company_id company, aat.type_order account_type_order from account_move_line aml
                    left join account_move am on aml.move_id = am.id
                    left join account_account aa on aml.account_id = aa.id
                    left join account_account_type aat on aa.user_type_id = aat.id %s""" % (
            filter_cdtn)

        self._cr.execute(query)
        profit_loss_ids = self._cr.dictfetchall()

        rows = []
        accounts = []
        lens = []

        for i in profit_loss_ids:
            rows.append({
                'acc_id': i['account_id'],
                'acc_code': i['account_code'],
                'acc_name': i['account_name'],
                'acc_debit': i['debit'],
                'acc_credit': i['credit'],
                'acc_type_id': i['account_type_id'],
                'acc_type_name': i['account_type_name'],
                'acc_type': i['account_type'],
                'acc_type_report': i['account_type_report'],
            })
            accounts.append({'data': {
                'acc_id': i['account_id'],
            }})
            lens.append({
                'acc_type_id': i['account_type_id'],
                'acc_type_name': i['account_type_name'],
                'acc_type': i['account_type'],
                'acc_type_report': i['account_type_report'],
                'acc_type_order': i['account_type_order'],
            })

        no_dup_lens = []
        for j in lens:
            if j not in no_dup_lens:
                no_dup_lens.append(j)

        no_dup_lens.sort(key=lambda z: z['acc_type_order'])

        no_dup_account = []
        for a in accounts:
            if a['data'] not in no_dup_account:
                no_dup_account.append(a['data'])

        inv = []
        for b in no_dup_account:
            chart_acc_id = b['acc_id']
            chart_acc_code = ''
            chart_acc_name = ''
            line_debit = 0
            line_credit = 0
            chart_type_id = ''
            chart_type_name = ''
            chart_type = ''
            chart_type_report = ''

            for c in rows:
                if c['acc_id'] == chart_acc_id:
                    chart_acc_code = c['acc_code']
                    chart_acc_name = c['acc_name']
                    line_debit += c['acc_debit']
                    line_credit += c['acc_credit']
                    chart_type_id = c['acc_type_id']
                    chart_type_name = c['acc_type_name']
                    chart_type = c['acc_type']
                    chart_type_report = c['acc_type_report']

            inv.append({
                'acc_id': chart_acc_id,
                'acc_code': chart_acc_code,
                'acc_name': chart_acc_name,
                'acc_debit': line_debit,
                'acc_credit': line_credit,
                'acc_type_id': chart_type_id,
                'acc_type_name': chart_type_name,
                'acc_type': chart_type,
                'acc_type_report': chart_type_report,
            })
        data = {
            'ids': self.ids,
            'model': self._name,
            'vals': inv,
            'type': no_dup_lens,
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
            'data': {'model': 'profit.loss.report.wizard',
                     'options': json.dumps(data, default=date_utils.json_default),
                     'output_format': 'xlsx',
                     'report_name': 'Profit & Loss Report',
                     },
            'report_type': 'xlsx',
        }

    def get_xlsx_report(self, data, response):
        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})

        row = 6
        col = 0
        sheet = workbook.add_worksheet('Profit & Loss')
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

        sheet.write(row - 1, col + 1, 'Expense', table_head1)
        sheet.write(row - 1, col + 2, 'Amount', table_head2)
        sheet.write(row - 1, col + 3, 'Income', table_head1)
        sheet.write(row - 1, col + 4, 'Amount', table_head2)

        sheet.merge_range('B2:E2',
                          str(data['company_name']) + '\n' + str(data['com_street']) + '\n' + str(
                              data['com_street2']) + '\n' + str(data[
                                                                    'com_city']) + ' ' + str(
                              data['com_state']) + ' ' + str(
                              data['com_zip']) + '\n' + str(
                              data['com_country']) + '\n' +
                          str(data['com_phone']) + '\n' + str(data['com_email']), com_address)
        sheet.merge_range('B3:E3', 'Profit & Loss', print_heading)
        sheet.merge_range('B4:E4', data['start'] + ' - ' + data['end'], print_heading)
        sheet.merge_range('B5:E5', '')

        row1 = 6
        for i in data['type']:
            if i['acc_type'] == 'expense':
                line_expense_sum = 0
                for j in data['vals']:
                    if j['acc_type_id'] == i['acc_type_id'] and j['acc_type'] == i['acc_type']:
                        line_expense_sum += (j['acc_debit'] - j['acc_credit'])
                sheet.write(row1, col + 1, ' ' + i['acc_type_name'], type_name_column)
                sheet.write(row1, col + 2, '%.2f' % line_expense_sum, type_amount_column)
                a = row1 + 1
                if data['summary'] == True:
                    for k in data['vals']:
                        if k['acc_type_id'] == i['acc_type_id'] and k['acc_type'] == i['acc_type']:
                            sheet.write(a, col + 1, '  ' + k['acc_code'] + ' ' + k['acc_name'], value_column)
                            sheet.write(a, col + 2, '%.2f' % (k['acc_debit'] - k['acc_credit']), table_amount_td)
                            a += 1
                row1 = a

        expense_total = 0
        for exp_tot in data['vals']:
            if exp_tot['acc_type'] == 'expense':
                expense_total += (exp_tot['acc_debit'] - exp_tot['acc_credit'])

        sheet.write(row1, col + 1, 'Total', table_head1)
        sheet.write(row1, col + 2, '%.2f' % expense_total, type_amount_column)

        row2 = 6
        for x in data['type']:
            if x['acc_type'] == 'income':
                line_income_sum = 0
                for y in data['vals']:
                    if y['acc_type_id'] == x['acc_type_id'] and y['acc_type'] == x['acc_type']:
                        line_income_sum += (y['acc_credit'] - y['acc_debit'])
                sheet.write(row2, col + 3, ' ' + x['acc_type_name'], type_name_column)
                sheet.write(row2, col + 4, '%.2f' % line_income_sum, type_amount_column)
                b = row2 + 1
                if data['summary'] == True:
                    for z in data['vals']:
                        if z['acc_type_id'] == x['acc_type_id'] and z['acc_type'] == x['acc_type']:
                            sheet.write(b, col + 3, '  ' + z['acc_code'] + ' ' + z['acc_name'], value_column)
                            sheet.write(b, col + 4, '%.2f' % (z['acc_credit'] - z['acc_debit']), table_amount_td)
                            b += 1
                row2 = b

        income_total = 0
        for in_tot in data['vals']:
            if in_tot['acc_type'] == 'income':
                income_total += (in_tot['acc_credit'] - in_tot['acc_debit'])
        sheet.write(row2, col + 3, 'Total', table_head1)
        sheet.write(row2, col + 4, '%.2f' % income_total, type_amount_column)

        gross_income_sum = 0
        gross_cost_of_revenue_sum = 0
        for g in data['vals']:
            if g['acc_type'] == 'expense' and g['acc_type_report'] == 'cost_of_revenue':
                gross_cost_of_revenue_sum += (g['acc_debit'] - g['acc_credit'])
            if g['acc_type'] == 'income' and g['acc_type_report'] == 'income':
                gross_income_sum += (g['acc_credit'] - g['acc_debit'])

        expense_value = 0
        income_value = 0
        for net_s in data['vals']:
            if net_s['acc_type'] == 'expense':
                expense_value += (net_s['acc_debit'] - net_s['acc_credit'])
            if net_s['acc_type'] == 'income':
                income_value += (net_s['acc_credit'] - net_s['acc_debit'])

        if row1 >= row2:
            gross_p = 'B' + str(row1 + 1) + ':' + 'E' + str(row1 + 1)
            sheet.set_row(row1, 35)
            sheet.merge_range(gross_p,
                              'Gross Profit' + '    ' + str('%.2f' % (gross_income_sum - gross_cost_of_revenue_sum)),
                              print_heading)
            net_p = 'B' + str(row1 + 2) + ':' + 'E' + str(row1 + 2)
            sheet.set_row(row1 + 1, 35)
            sheet.merge_range(net_p, 'Net Profit' + '    ' + str('%.2f' % (income_value - expense_value)),
                              print_heading)
            current_print = 'B' + str(row1 + 3) + ':' + 'E' + str(row1 + 3)
            sheet.set_row(row1 + 2, 20)
            sheet.merge_range(current_print, data['user_name'] + ' ' + '-' + ' ' + data['current_date'], foot)
        else:
            gross_p = 'B' + str(row2 + 1) + ':' + 'E' + str(row2 + 1)
            sheet.set_row(row2, 35)
            sheet.merge_range(gross_p,
                              'Gross Profit' + '    ' + str('%.2f' % (gross_income_sum - gross_cost_of_revenue_sum)),
                              print_heading)
            net_p = 'B' + str(row2 + 2) + ':' + 'E' + str(row2 + 2)
            sheet.set_row(row2 + 1, 35)
            sheet.merge_range(net_p, 'Net Profit' + '    ' + str('%.2f' % (income_value - expense_value)),
                              print_heading)
            current_print = 'B' + str(row2 + 3) + ':' + 'E' + str(row2 + 3)
            sheet.set_row(row2 + 2, 20)
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
