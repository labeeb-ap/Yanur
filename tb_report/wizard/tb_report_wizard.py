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


class TBReportWizard(models.TransientModel):
    _name = "tb.report.wizard"
    _description = "TB Report"

    date_from = fields.Date(string='From Date', default=date.today())
    date_to = fields.Date(string='To Date', default=date.today())
    company_ids = fields.Many2many('res.company', string='Company')
    detailed_summary = fields.Boolean(string="Detailed Summary", store=True)

    def action_print_report(self):
        if self.date_from > self.date_to:
            raise Warning(_("From Date is GreaterThan To Date"))
        else:
            filter_cdtn = '''where am.state = 'posted' and am.move_type = 'entry'
                             '''
        if self.company_ids:
            if len(self.company_ids) == 1:
                filter_cdtn += '''and aml.company_id = '%s'
                ''' % (self.company_ids.ids[0])
            else:
                filter_cdtn += '''and aml.company_id in {}
                '''.format(tuple(self.company_ids.ids))

        query = """select aml.date acc_date, aa.id acc_account, aa.code acc_code, aa.name acc_name, aml.debit acc_debit,
            aml.credit acc_credit, aml.company_id acc_company, aat.id acc_type_id, aat.name acc_type_name,
            aat.type_order acc_type_order from account_move_line aml
            left join account_move am on aml.move_id = am.id
            left join account_account aa on aml.account_id = aa.id
			left join account_account_type aat on aa.user_type_id = aat.id %s""" % (
            filter_cdtn)

        self._cr.execute(query)
        tb_account_ids = self._cr.dictfetchall()

        main_values = []
        lens = []
        initial = []
        initial_account = []
        acc_types = []
        for i in tb_account_ids:
            if i['acc_date'] >= self.date_from and i['acc_date'] <= self.date_to:
                main_values.append({
                    'line_date': i['acc_date'],
                    'line_account': i['acc_account'],
                    'line_code': i['acc_code'],
                    'line_name': i['acc_name'],
                    'line_debit': i['acc_debit'],
                    'line_credit': i['acc_credit'],
                    'line_type_id': i['acc_type_id'],
                })
                lens.append({
                    'line_account': i['acc_account'],
                })
                acc_types.append({'data': {
                    'line_type_id': i['acc_type_id'],
                    'line_type_name': i['acc_type_name'],
                    'line_type_code': i['acc_type_order'],
                }})

            if i['acc_date'] < self.date_from:
                initial.append({
                    'ini_account': i['acc_account'],
                    'ini_debit': i['acc_debit'],
                    'ini_credit': i['acc_credit'],
                })
                initial_account.append({
                    'line_account': i['acc_account'],
                })

        no_dup_types = []
        for no_t in acc_types:
            if no_t['data'] not in no_dup_types:
                no_dup_types.append(no_t['data'])

        no_dup_types.sort(key=lambda z: z['line_type_code'])

        no_lens = []
        no_dup_initial = []
        for j in lens:
            if j not in no_lens:
                no_lens.append(j)

        for k in initial_account:
            if k not in no_dup_initial:
                no_dup_initial.append(k)

        inv1 = []
        for a in no_lens:
            chart_acc_id = a['line_account']
            chart_acc_code = ''
            chart_acc_name = ''
            debit = 0
            credit = 0
            chart_type_id = ''

            for b in main_values:
                if b['line_account'] == chart_acc_id:
                    chart_acc_code = b['line_code']
                    chart_acc_name = b['line_name']
                    debit += b['line_debit']
                    credit += b['line_credit']
                    chart_type_id = b['line_type_id']

            inv1.append({
                'acc_id': chart_acc_id,
                'acc_code': chart_acc_code,
                'acc_name': chart_acc_name,
                'acc_debit': debit,
                'acc_credit': credit,
                'account_type_id': chart_type_id,
            })

        inv2 = []
        for c in no_dup_initial:
            i_acc_id = c['line_account']
            i_debit = 0
            i_credit = 0

            for d in initial:
                if d['ini_account'] == i_acc_id:
                    i_debit += d['ini_debit']
                    i_credit += d['ini_credit']

            inv2.append({
                'ini_account': i_acc_id,
                'ini_debit': i_debit,
                'ini_credit': i_credit,
            })

        inv_final = []
        for x in inv1:
            final_acc_id = x['acc_id']
            final_acc_code = x['acc_code']
            final_acc_name = x['acc_name']
            final_acc_debit = x['acc_debit']
            final_acc_credit = x['acc_credit']
            f_debit = 0
            f_credit = 0
            final_account_type_id = x['account_type_id']
            for y in inv2:
                if y['ini_account'] == final_acc_id:
                    f_debit = y['ini_debit']
                    f_credit = y['ini_credit']
            inv_final.append({
                'acc_id': final_acc_id,
                'acc_code': final_acc_code,
                'acc_name': final_acc_name,
                'acc_debit': final_acc_debit,
                'acc_credit': final_acc_credit,
                'i_debit': f_debit,
                'i_credit': f_credit,
                'account_type_id': final_account_type_id,
            })

        data = {
            'ids': self.ids,
            'model': self._name,
            'vals': inv_final,
            'd_from': self.date_from.strftime("%d-%b-%Y"),
            'd_to': self.date_to.strftime("%d-%b-%Y"),
            'type': no_dup_types,
            'summary': self.detailed_summary,
        }
        action = self.env.ref('tb_report.t_b_report_pdf').report_action(self, data=data)
        # action.update({'close_on_report_download': True})
        return action

    def print_xl_report(self):
        if self.date_from > self.date_to:
            raise Warning(_("From Date is GreaterThan To Date"))
        else:
            filter_cdtn = '''where am.state = 'posted' and am.move_type = 'entry'
                                     '''
        if self.company_ids:
            if len(self.company_ids) == 1:
                filter_cdtn += '''and aml.company_id = '%s'
                        ''' % (self.company_ids.ids[0])
            else:
                filter_cdtn += '''and aml.company_id in {}
                        '''.format(tuple(self.company_ids.ids))

        query = """select aml.date acc_date, aa.id acc_account, aa.code acc_code, aa.name acc_name, aml.debit acc_debit,
                    aml.credit acc_credit, aml.company_id acc_company, aat.id acc_type_id, aat.name acc_type_name,
                    aat.type_order acc_type_order from account_move_line aml
                    left join account_move am on aml.move_id = am.id
                    left join account_account aa on aml.account_id = aa.id
        			left join account_account_type aat on aa.user_type_id = aat.id %s""" % (
            filter_cdtn)

        self._cr.execute(query)
        tb_account_ids = self._cr.dictfetchall()

        main_values = []
        lens = []
        initial = []
        initial_account = []
        acc_types = []
        for i in tb_account_ids:
            if i['acc_date'] >= self.date_from and i['acc_date'] <= self.date_to:
                main_values.append({
                    'line_date': i['acc_date'],
                    'line_account': i['acc_account'],
                    'line_code': i['acc_code'],
                    'line_name': i['acc_name'],
                    'line_debit': i['acc_debit'],
                    'line_credit': i['acc_credit'],
                    'line_type_id': i['acc_type_id'],
                })
                lens.append({
                    'line_account': i['acc_account'],
                })
                acc_types.append({'data': {
                    'line_type_id': i['acc_type_id'],
                    'line_type_name': i['acc_type_name'],
                    'line_type_code': i['acc_type_order'],
                }})

            if i['acc_date'] < self.date_from:
                initial.append({
                    'ini_account': i['acc_account'],
                    'ini_debit': i['acc_debit'],
                    'ini_credit': i['acc_credit'],
                })
                initial_account.append({
                    'line_account': i['acc_account'],
                })

        no_dup_types = []
        for no_t in acc_types:
            if no_t['data'] not in no_dup_types:
                no_dup_types.append(no_t['data'])

        no_dup_types.sort(key=lambda z: z['line_type_code'])

        no_lens = []
        no_dup_initial = []
        for j in lens:
            if j not in no_lens:
                no_lens.append(j)

        for k in initial_account:
            if k not in no_dup_initial:
                no_dup_initial.append(k)

        inv1 = []
        for a in no_lens:
            chart_acc_id = a['line_account']
            chart_acc_code = ''
            chart_acc_name = ''
            debit = 0
            credit = 0
            chart_type_id = ''

            for b in main_values:
                if b['line_account'] == chart_acc_id:
                    chart_acc_code = b['line_code']
                    chart_acc_name = b['line_name']
                    debit += b['line_debit']
                    credit += b['line_credit']
                    chart_type_id = b['line_type_id']

            inv1.append({
                'acc_id': chart_acc_id,
                'acc_code': chart_acc_code,
                'acc_name': chart_acc_name,
                'acc_debit': debit,
                'acc_credit': credit,
                'account_type_id': chart_type_id,
            })

        inv2 = []
        for c in no_dup_initial:
            i_acc_id = c['line_account']
            i_debit = 0
            i_credit = 0

            for d in initial:
                if d['ini_account'] == i_acc_id:
                    i_debit += d['ini_debit']
                    i_credit += d['ini_credit']

            inv2.append({
                'ini_account': i_acc_id,
                'ini_debit': i_debit,
                'ini_credit': i_credit,
            })

        inv_final = []
        for x in inv1:
            final_acc_id = x['acc_id']
            final_acc_code = x['acc_code']
            final_acc_name = x['acc_name']
            final_acc_debit = x['acc_debit']
            final_acc_credit = x['acc_credit']
            f_debit = 0
            f_credit = 0
            final_account_type_id = x['account_type_id']
            for y in inv2:
                if y['ini_account'] == final_acc_id:
                    f_debit = y['ini_debit']
                    f_credit = y['ini_credit']
            inv_final.append({
                'acc_id': final_acc_id,
                'acc_code': final_acc_code,
                'acc_name': final_acc_name,
                'acc_debit': final_acc_debit,
                'acc_credit': final_acc_credit,
                'i_debit': f_debit,
                'i_credit': f_credit,
                'account_type_id': final_account_type_id,
            })

        data = {
            'ids': self.ids,
            'model': self._name,
            'vals': inv_final,
            'd_from': self.date_from.strftime("%d-%b-%Y"),
            'd_to': self.date_to.strftime("%d-%b-%Y"),
            'type': no_dup_types,
            'summary': self.detailed_summary,

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
            'data': {'model': 'tb.report.wizard',
                     'options': json.dumps(data, default=date_utils.json_default),
                     'output_format': 'xlsx',
                     'report_name': 'Trial Balance Report',
                     },
            'report_type': 'xlsx',
        }

    def get_xlsx_report(self, data, response):
        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})

        row = 6
        col = 0
        sheet = workbook.add_worksheet('Trial Balance')
        print_heading = workbook.add_format(
            {'bold': True, 'align': 'center', 'valign': 'vcenter', 'font_size': 13, 'bg_color': '#DEE9FF', 'border': 1})
        table_main_td1 = workbook.add_format(
            {'bold': True, 'align': 'left', 'valign': 'vcenter', 'border': 1})
        table_main_td2 = workbook.add_format(
            {'bold': True, 'align': 'right', 'valign': 'vcenter', 'border': 1})
        type_amount_column = workbook.add_format(
            {'align': 'right', 'valign': 'vcenter', 'border': 1})
        report_name_column = workbook.add_format(
            {'bold': True, 'valign': 'vcenter', 'align': 'center', 'border': 1, 'bg_color': '#DEE9FF'})
        date_column = workbook.add_format({'valign': 'vcenter', 'border': 1, 'align': 'center'})
        com_address = workbook.add_format({'valign': 'vcenter', 'align': 'center', 'font_size': 14, 'border': 1})
        foot = workbook.add_format(
            {'bold': True, 'align': 'right', 'valign': 'vcenter', 'font_size': 13, 'bg_color': '#DEE9FF', 'border': 1})
        head_acc_name = workbook.add_format(
            {'valign': 'vcenter', 'border': 1})

        sheet.write(row - 1, col + 1, 'Account', print_heading)
        sheet.write(row - 1, col + 2, 'Initial Debit', print_heading)
        sheet.write(row - 1, col + 3, 'Initial Credit', print_heading)
        sheet.write(row - 1, col + 4, 'Debit', print_heading)
        sheet.write(row - 1, col + 5, 'Credit', print_heading)
        sheet.write(row - 1, col + 6, 'Total Debit', print_heading)
        sheet.write(row - 1, col + 7, 'Total Credit', print_heading)

        sheet.merge_range('B2:H2',
                          str(data['company_name']) + '\n' + str(data['com_street']) + '\n' + str(
                              data['com_street2']) + '\n' + str(data[
                                                                    'com_city']) + ' ' + str(
                              data['com_state']) + ' ' + str(
                              data['com_zip']) + '\n' + str(
                              data['com_country']) + '\n' +
                          str(data['com_phone']) + '\n' + str(data['com_email']), com_address)
        sheet.merge_range('B3:H3', 'Trial Balance', report_name_column)
        sheet.merge_range('B4:H4', data['d_from'] + ' - ' + data['d_to'], date_column)
        sheet.merge_range('B5:H5', '')

        row1 = 6
        for i in data['type']:
            in_debit = 0
            in_credit = 0
            deb = 0
            cre = 0
            to_debit = 0
            to_credit = 0
            for j in data['vals']:
                if j['account_type_id'] == i['line_type_id']:
                    in_debit += j['i_debit']
                    in_credit += j['i_credit']
                    deb += j['acc_debit']
                    cre += j['acc_credit']
                    to_debit += (j['i_debit'] + j['acc_debit'])
                    to_credit += (j['i_credit'] + j['acc_credit'])
            sheet.write(row1, col + 1, ' ' + i['line_type_name'], table_main_td1)
            sheet.write(row1, col + 2, ('%.2f' % in_debit) + ' ', table_main_td2)
            sheet.write(row1, col + 3, ('%.2f' % in_credit) + ' ', table_main_td2)
            sheet.write(row1, col + 4, ('%.2f' % deb) + ' ', table_main_td2)
            sheet.write(row1, col + 5, ('%.2f' % cre) + ' ', table_main_td2)
            sheet.write(row1, col + 6, ('%.2f' % to_debit) + ' ', table_main_td2)
            sheet.write(row1, col + 7, ('%.2f' % to_credit) + ' ', table_main_td2)
            a = row1 + 1
            if data['summary'] == True:
                for k in data['vals']:
                    if k['account_type_id'] == i['line_type_id']:
                        sheet.write(a, col + 1, '  ' + k['acc_code'] + ' ' + k['acc_name'], head_acc_name)
                        sheet.write(a, col + 2, ('%.2f' % k['i_debit']) + ' ', type_amount_column)
                        sheet.write(a, col + 3, ('%.2f' % k['i_credit']) + ' ', type_amount_column)
                        sheet.write(a, col + 4, ('%.2f' % k['acc_debit']) + ' ', type_amount_column)
                        sheet.write(a, col + 5, ('%.2f' % k['acc_credit']) + ' ', type_amount_column)
                        sheet.write(a, col + 6, ('%.2f' % (k['i_debit'] + k['acc_debit'])) + ' ', type_amount_column)
                        sheet.write(a, col + 7, ('%.2f' % (k['i_credit'] + k['acc_credit'])) + ' ', type_amount_column)
                        a += 1
            row1 = a
        final_total_ini_debit = 0
        final_total_ini_credit = 0
        final_deb = 0
        final_cre = 0
        final_debit = 0
        final_credit = 0
        for f in data['vals']:
            final_total_ini_debit += f['i_debit']
            final_total_ini_credit += f['i_credit']
            final_deb += f['acc_debit']
            final_cre += f['acc_credit']
            final_debit += (f['i_debit'] + f['acc_debit'])
            final_credit += (f['i_credit'] + f['acc_credit'])
        sheet.write(row1, col + 1, 'Total', print_heading)
        sheet.write(row1, col + 2, ('%.2f' % final_total_ini_debit) + ' ', foot)
        sheet.write(row1, col + 3, ('%.2f' % final_total_ini_credit) + ' ', foot)
        sheet.write(row1, col + 4, ('%.2f' % final_deb) + ' ', foot)
        sheet.write(row1, col + 5, ('%.2f' % final_cre) + ' ', foot)
        sheet.write(row1, col + 6, ('%.2f' % final_debit) + ' ', foot)
        sheet.write(row1, col + 7, ('%.2f' % final_credit) + ' ', foot)

        sheet.set_row(row1, 35)

        just_print = 'B' + str(row1 + 2) + ':' + 'H' + str(row1 + 2)
        sheet.merge_range(just_print, '')

        current_print = 'B' + str(row1 + 3) + ':' + 'H' + str(row1 + 3)
        sheet.set_row(row1 + 2, 20)
        sheet.merge_range(current_print, data['user_name'] + ' ' + '-' + ' ' + data['current_date'], date_column)

        sheet.set_column('B:B', 50)
        sheet.set_column('C:C', 20)
        sheet.set_column('D:D', 20)
        sheet.set_column('E:E', 20)
        sheet.set_column('F:F', 20)
        sheet.set_column('G:G', 20)
        sheet.set_column('H:H', 20)

        sheet.set_row(1, 125)
        sheet.set_row(2, 35)
        sheet.set_row(3, 35)
        sheet.set_row(5, 35)

        workbook.close()
        output.seek(0)
        response.stream.write(output.read())
        output.close()
