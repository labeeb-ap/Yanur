import io

from odoo import models, fields, _, api
from datetime import date, datetime
from odoo.exceptions import Warning
from odoo.http import request
from odoo.tools import date_utils
from odoo.tools.safe_eval import json

try:
    from odoo.tools.misc import xlsxwriter
except ImportError:
    import xlsxwriter


class CashAccountReportWizard(models.TransientModel):
    _name = "cash.account.report.wizard"
    _description = "Cash Account Report"

    date_from = fields.Date(string='From Date', default=date.today())
    date_to = fields.Date(string='To Date', default=date.today())
    account_id = fields.Many2one('account.account', string='Account Head',
                                 domain=[('user_type_id.name', '=', 'Bank and Cash')])
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.company.id)
    user_id = fields.Many2one('res.users', string='User', default=lambda self: self.env.user.id)

    is_label = fields.Boolean(string='Label')
    is_partner = fields.Boolean(string='Partner')
    is_account = fields.Boolean(string='A/c head')

    def action_print_report(self):
        if self.date_from > self.date_to:
            raise Warning(_("From Date is GreaterThan To Date"))
        if self.account_id:
            filter_cdtn = '''where account_move.move_type = 'entry' and aml.parent_state = 'posted'
	            and account_account_type.name = 'Bank and Cash'
	            and aml.account_id = '%s'
                ''' % self.account_id.id

        query = """SELECT distinct(aml.account_id) as chart_id
	                    FROM account_move_line as aml
                        left join account_account on aml.account_id = account_account.id
	                    left join account_account_type on account_account.user_type_id = account_account_type.id
	                    left join account_move on aml.move_id = account_move.id %s""" % (
            filter_cdtn)

        self._cr.execute(query)
        cash_account_ids = self._cr.dictfetchall()

        acc_id = []
        for k in cash_account_ids:
            acc_id.append(k['chart_id'])

        open_list = []
        close_list = []
        main_list = []
        if acc_id:
            sum_open = self.env['account.move'].search(
                [('line_ids.account_id', '=', acc_id[0]), ('move_type', '=', 'entry'),
                 ('state', '=', 'posted'), ('line_ids.date', '<', self.date_from)])
            for o in sum_open:
                open_list.append(o)

            sum_close = self.env['account.move'].search(
                [('line_ids.account_id', '=', acc_id[0]), ('move_type', '=', 'entry'),
                 ('state', '=', 'posted'), ('line_ids.date', '<=', self.date_to)])
            for c in sum_close:
                close_list.append(c)

            acc_main = self.env['account.move'].search(
                [('line_ids.account_id', '=', acc_id[0]), ('move_type', '=', 'entry'),
                 ('state', '=', 'posted'), ('line_ids.date', '>=', self.date_from),
                 ('line_ids.date', '<=', self.date_to)], order='date asc')
            for main in acc_main:
                main_list.append(main)

        dup_open = set(open_list)
        dup_close = set(close_list)
        dup_main = set(main_list)

        open_debit = 0
        open_credit = 0
        if acc_id:
            for s in dup_open:
                for s_line in s.line_ids:
                    if acc_id[0] == s_line.account_id.id:
                        open_debit += s_line.debit
                        open_credit += s_line.credit
        open_sum = open_debit - open_credit

        close_debit = 0
        close_credit = 0
        if acc_id:
            for c_s in dup_close:
                for d_line in c_s.line_ids:
                    if acc_id[0] == d_line.account_id.id:
                        close_debit += d_line.debit
                        close_credit += d_line.credit
        close_sum = close_debit - close_credit

        rows = []
        lens = []
        if acc_id:
            for v in dup_main:
                for values in v.line_ids:
                    rows.append({
                        'main_entry': values.move_id.id,
                        'account_id': values.account_id.id,
                        'voucher_date': values.date,
                        'voucher': values.move_name,
                        'co': values.account_id.code,
                        'acc': values.account_id.name,
                        'partner': values.partner_id.name,
                        'label': values.name,
                        'debit': values.debit,
                        'credit': values.credit,
                    })
                    lens.append({
                        'main_entry': values.move_id.id,
                    })

        no_lens = []
        for j in lens:
            if j not in no_lens:
                no_lens.append(j)

        inv = []
        inv_inv = []
        for v in no_lens:
            main_id = v['main_entry']
            entry_date = ''
            entry_name = ''
            acc_debit = 0
            acc_credit = 0

            inv_dup = []
            for t in rows:
                if acc_id:
                    if t['main_entry'] == main_id:
                        entry_date = t['voucher_date']
                        entry_name = t['voucher']
                        if t['account_id'] != acc_id[0]:
                            inv_dup.append({
                                'entry_code': t['co'],
                                'entry_head': t['acc'],
                                'line_debit': t['debit'],
                                'line_credit': t['credit'],
                                'line_partner': t['partner'],
                                'line_label': t['label'],
                            })
                        if t['account_id'] == acc_id[0]:
                            acc_debit += t['debit']
                            acc_credit += t['credit']
            inv.append({
                # 'voucher_date': entry_date.strftime("%d-%m-%Y"),
                'voucher_date': entry_date,
                'voucher': entry_name,
                'values': inv_dup,
                'line_account_debit': acc_debit,
                'line_account_credit': acc_credit,
            })
        inv.sort(key=lambda x: x['voucher_date'])

        for d in inv:
            inv_inv.append({
                'voucher_date': d['voucher_date'].strftime("%d-%m-%Y"),
                'voucher': d['voucher'],
                'values': d['values'],
                'line_account_debit': d['line_account_debit'],
                'line_account_credit': d['line_account_credit'],
            })

        data = {
            'ids': self.ids,
            'model': self._name,
            # 'val': inv,
            'val': inv_inv,
            'open': open_sum,
            'close': close_sum,
            'date_f': self.date_from.strftime("%d-%b-%Y"),
            'date_t': self.date_to.strftime("%d-%b-%Y"),
            'type_name': self.account_id.name,
            'type_code': self.account_id.code,

            # 'user_name': self.user_id.name,
            # 'current_date': datetime.today().strftime("%d-%b-%Y %H:%M:%S"),

            'company_name': self.company_id.name,
            'com_street': self.company_id.street,
            'com_street2': self.company_id.street2,
            'com_city': self.company_id.city,
            'com_state': self.company_id.state_id.name,
            'com_zip': self.company_id.zip,
            'com_country': self.company_id.country_id.name,
            'com_phone': self.company_id.phone,
            'com_email': self.company_id.email,

            'is_account': self.is_account,
            'is_partner': self.is_partner,
            'is_label': self.is_label,
        }
        action = self.env.ref('cash_ac_report.cash_account_report_pdf').report_action(self, data=data)
        action.update({'close_on_report_download': True})
        return action

    def print_xl_report(self):
        if self.date_from > self.date_to:
            raise Warning(_("From Date is GreaterThan To Date"))
        if self.account_id:
            filter_cdtn = '''where account_move.move_type = 'entry' and aml.parent_state = 'posted'
        	            and account_account_type.name = 'Bank and Cash'
        	            and aml.account_id = '%s'
                        ''' % self.account_id.id

        query = """SELECT distinct(aml.account_id) as chart_id
        	                    FROM account_move_line as aml
                                left join account_account on aml.account_id = account_account.id
        	                    left join account_account_type on account_account.user_type_id = account_account_type.id
        	                    left join account_move on aml.move_id = account_move.id %s""" % (
            filter_cdtn)

        self._cr.execute(query)
        cash_account_ids = self._cr.dictfetchall()

        acc_id = []
        for k in cash_account_ids:
            acc_id.append(k['chart_id'])

        open_list = []
        close_list = []
        main_list = []
        if acc_id:
            sum_open = self.env['account.move'].search(
                [('line_ids.account_id', '=', acc_id[0]), ('move_type', '=', 'entry'),
                 ('state', '=', 'posted'), ('line_ids.date', '<', self.date_from)])
            for o in sum_open:
                open_list.append(o)

            sum_close = self.env['account.move'].search(
                [('line_ids.account_id', '=', acc_id[0]), ('move_type', '=', 'entry'),
                 ('state', '=', 'posted'), ('line_ids.date', '<=', self.date_to)])
            for c in sum_close:
                close_list.append(c)

            acc_main = self.env['account.move'].search(
                [('line_ids.account_id', '=', acc_id[0]), ('move_type', '=', 'entry'),
                 ('state', '=', 'posted'), ('line_ids.date', '>=', self.date_from),
                 ('line_ids.date', '<=', self.date_to)], order='date asc')
            for main in acc_main:
                main_list.append(main)

        dup_open = set(open_list)
        dup_close = set(close_list)
        dup_main = set(main_list)

        open_debit = 0
        open_credit = 0
        if acc_id:
            for s in dup_open:
                for s_line in s.line_ids:
                    if acc_id[0] == s_line.account_id.id:
                        open_debit += s_line.debit
                        open_credit += s_line.credit
        open_sum = open_debit - open_credit

        close_debit = 0
        close_credit = 0
        if acc_id:
            for c_s in dup_close:
                for d_line in c_s.line_ids:
                    if acc_id[0] == d_line.account_id.id:
                        close_debit += d_line.debit
                        close_credit += d_line.credit
        close_sum = close_debit - close_credit

        rows = []
        lens = []
        if acc_id:
            for v in dup_main:
                for values in v.line_ids:
                    rows.append({
                        'main_entry': values.move_id.id,
                        'account_id': values.account_id.id,
                        'voucher_date': values.date,
                        'voucher': values.move_name,
                        'co': values.account_id.code,
                        'acc': values.account_id.name,
                        'partner': values.partner_id.name,
                        'label': values.name,
                        'debit': values.debit,
                        'credit': values.credit,
                    })
                    lens.append({
                        'main_entry': values.move_id.id,
                    })

        no_lens = []
        for j in lens:
            if j not in no_lens:
                no_lens.append(j)

        inv = []
        inv_inv = []
        for v in no_lens:
            main_id = v['main_entry']
            entry_date = ''
            entry_name = ''
            acc_debit = 0
            acc_credit = 0

            inv_dup = []
            for t in rows:
                if acc_id:
                    if t['main_entry'] == main_id:
                        entry_date = t['voucher_date']
                        entry_name = t['voucher']
                        if t['account_id'] != acc_id[0]:
                            inv_dup.append({
                                'entry_code': t['co'],
                                'entry_head': t['acc'],
                                'line_debit': t['debit'],
                                'line_credit': t['credit'],
                                'line_partner': t['partner'],
                                'line_label': t['label'],
                            })
                        if t['account_id'] == acc_id[0]:
                            acc_debit += t['debit']
                            acc_credit += t['credit']

            inv.append({
                # 'voucher_date': entry_date.strftime("%d-%m-%Y"),
                'voucher_date': entry_date,
                'voucher': entry_name,
                'values': inv_dup,
                'line_account_debit': acc_debit,
                'line_account_credit': acc_credit,
            })
        inv.sort(key=lambda x: x['voucher_date'])

        for d in inv:
            inv_inv.append({
                'voucher_date': d['voucher_date'].strftime("%d-%m-%Y"),
                'voucher': d['voucher'],
                'values': d['values'],
                'line_account_debit': d['line_account_debit'],
                'line_account_credit': d['line_account_credit'],
            })
        data = {
            # 'val': inv,
            'val': inv_inv,
            'open': open_sum,
            'close': close_sum,
            'date_f': self.date_from.strftime("%d-%b-%Y"),
            'date_t': self.date_to.strftime("%d-%b-%Y"),
            'type_name': self.account_id.name,
            'type_code': self.account_id.code,

            'user_name': self.user_id.name,
            'current_date': fields.Datetime.context_timestamp(self, fields.Datetime.now()).strftime('%d/%m/%Y %H:%M'),

            'company_name': self.company_id.name,
            'com_street': self.company_id.street,
            'com_street2': self.company_id.street2,
            'com_city': self.company_id.city,
            'com_state': self.company_id.state_id.name,
            'com_zip': self.company_id.zip,
            'com_country': self.company_id.country_id.name,
            'com_phone': self.company_id.phone,
            'com_email': self.company_id.email,
        }
        return {
            'type': 'ir.actions.report',
            'data': {'model': 'cash.account.report.wizard',
                     'options': json.dumps(data, default=date_utils.json_default),
                     'output_format': 'xlsx',
                     'report_name': 'Cash Account Report',
                     },
            'report_type': 'xlsx',
        }

    def get_xlsx_report(self, data, response):
        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})
        # wizard_record = request.env['cash.account.report.wizard'].search([])[-1]

        row = 6
        col = 0
        sheet = workbook.add_worksheet('Cash Account')
        table_head = workbook.add_format(
            {'bold': True, 'bg_color': '#bfbbbd', 'align': 'center', 'valign': 'vcenter', 'border': 1, 'font_size': 14})
        bold2 = workbook.add_format({'bold': True, 'align': 'center', 'font_size': 13, 'valign': 'vcenter'})
        bold1 = workbook.add_format({'bold': True, 'font_size': 13, 'valign': 'vcenter'})
        size = workbook.add_format(
            {'bold': True, 'font_size': 18, 'align': 'center', 'bg_color': '#bfbbbd', 'valign': 'vcenter'})
        balance = workbook.add_format({'bold': True, 'font_size': 16, 'align': 'center', 'valign': 'vcenter'})
        td_right = workbook.add_format({'align': 'right', 'valign': 'vcenter', 'border': 1})
        td_center = workbook.add_format({'valign': 'vcenter', 'border': 1})
        footer = workbook.add_format({'valign': 'vcenter', 'align': 'center'})
        com_address = workbook.add_format({'valign': 'vcenter', 'align': 'center', 'font_size': 14})

        sheet.write(row - 2, col + 0, 'Date From :', bold2)
        sheet.write(row - 2, col + 1, ' ' + data['date_f'], bold1)
        sheet.write(row - 2, col + 3, 'Date To :', bold2)
        sheet.write(row - 2, col + 4, ' ' + data['date_t'], bold1)
        sheet.write(row - 2, col + 6, 'A/c Head :', bold2)
        sheet.write(row - 2, col + 7, ' ' + data['type_code'] + ' ' + data['type_name'], bold1)
        if data['open'] == 0:
            sheet.write(row + 0, col + 0, 'Opening Balance : ' + str(data['open']), balance)
        else:
            if data['open'] < 0:
                sheet.write(row + 0, col + 0, 'Opening Balance : ' + str('%.2f' % (data['open'])) + ' Cr', balance)
            if data['open'] > 0:
                sheet.write(row + 0, col + 0, 'Opening Balance : ' + str('%.2f' % (data['open'])) + ' Dr', balance)

        sheet.merge_range('A3:H3', 'Cash Account Report', size)
        sheet.merge_range('A4:H4',
                          str(data['company_name']) + '\n' + str(data['com_street']) + '\n' + str(
                              data['com_street2']) + '\n' + str(data[
                                                                    'com_city']) + ' ' + str(
                              data['com_state']) + ' ' + str(
                              data['com_zip']) + '\n' + str(
                              data['com_country']) + '\n' +
                          str(data['com_phone']) + '\n' + str(data['com_email']), com_address)
        sheet.merge_range('A7:H7', '', )

        sheet.merge_range('A1:H1', '', )
        sheet.merge_range('A2:H2', '', )
        sheet.merge_range('A6:H6', '', )

        sheet.write(row + 2, col + 0, 'Date', table_head)
        sheet.write(row + 2, col + 1, 'Voucher No.', table_head)
        sheet.write(row + 2, col + 2, 'A/c Head', table_head)
        sheet.write(row + 2, col + 3, 'Partner', table_head)
        sheet.write(row + 2, col + 4, 'Label', table_head)
        sheet.write(row + 2, col + 5, 'Debit', table_head)
        sheet.write(row + 2, col + 6, 'Credit', table_head)
        sheet.write(row + 2, col + 7, 'Cumulative Balance', table_head)

        sheet.set_column('A:A', 16)
        sheet.set_column('B:B', 20)
        sheet.set_column('C:C', 45)
        sheet.set_column('D:D', 30)
        sheet.set_column('E:E', 35)
        sheet.set_column('F:F', 14)
        sheet.set_column('G:G', 14)
        sheet.set_column('H:H', 45)

        sheet.set_row(2, 35)
        sheet.set_row(3, 115)
        sheet.set_row(6, 35)
        sheet.set_row(8, 35)
        sheet.set_row(4, 35)

        if data['open'] == 0:
            cumulative = 0
        else:
            cumulative = data['open']

        for i in data['val']:
            sheet.set_row(row + 3, 40)
            sheet.write(row + 3, col + 0, ' ' + i['voucher_date'], td_center)
            sheet.write(row + 3, col + 1, ' ' + i['voucher'], td_center)
            sl_no = 0
            acc_value = []
            for j in i['values']:
                sl_no += 1
                if j['line_debit'] != 0:
                    a1 = str(sl_no) + '. ' + str(j['entry_code']) + ' ' + str(j['entry_head']) + ' - ' + str(
                        j['line_debit']) + ' Dr'
                    acc_value.append(a1)
                if j['line_credit'] != 0:
                    a2 = str(sl_no) + '. ' + str(j['entry_code']) + ' ' + str(j['entry_head']) + ' - ' + str(
                        j['line_credit']) + ' Cr'
                    acc_value.append(a2)
                if j['line_debit'] == 0 and j['line_credit'] == 0:
                    a3 = str(sl_no) + '. ' + str(j['entry_code']) + ' ' + str(j['entry_head'])
                    acc_value.append(a3)
            sheet.write(row + 3, col + 2, ' ' + '\n '.join(map(lambda x: x, acc_value)), td_center)

            part_no = 0
            partner_value = []
            for k in i['values']:
                part_no += 1
                if k['line_partner']:
                    l2 = str(part_no) + '. ' + str(k['line_partner'])
                    partner_value.append(l2)
            sheet.write(row + 3, col + 3, ' ' + '\n '.join(map(lambda x: x, partner_value)), td_center)

            label_no = 0
            label_value = []
            for lab in i['values']:
                label_no += 1
                if lab['line_label']:
                    l1 = str(label_no) + '. ' + str(lab['line_label'])
                    label_value.append(l1)
            sheet.write(row + 3, col + 4, ' ' + '\n '.join(map(lambda x: x, label_value)), td_center)

            sheet.write(row + 3, col + 5, '%.2f' % i['line_account_debit'] + ' ', td_right)
            sheet.write(row + 3, col + 6, '%.2f' % i['line_account_credit'] + ' ', td_right)
            # if i['line_account_debit'] != 0:
            #     cumulative += i['line_account_debit']
            #     sheet.write(row + 3, col + 7, '%.2f' % cumulative + ' ', td_right)
            # if i['line_account_credit'] != 0:
            #     cumulative -= i['line_account_credit']
            #     sheet.write(row + 3, col + 7, '%.2f' % cumulative + ' ', td_right)
            # if i['line_account_debit'] == 0 and i['line_account_credit'] == 0:
            #     sheet.write(row + 3, col + 7, '', td_right)
            cumulative += i['line_account_debit'] - i['line_account_credit']
            sheet.write(row + 3, col + 7, '%.2f' % cumulative + ' ', td_right)
            row += 1

        p = 'A' + str(row + 5) + ':' + 'H' + str(row + 5)
        sheet.set_row(row + 4, 35)

        if data['close'] == 0:
            sheet.merge_range(p, 'Closing Balance : ' + str(data['close']), balance)
        else:
            if data['close'] < 0:
                sheet.merge_range(p, 'Closing Balance : ' + str('%.2f' % (data['close'])) + ' Cr', balance)
            if data['close'] > 0:
                sheet.merge_range(p, 'Closing Balance : ' + str('%.2f' % (data['close'])) + ' Dr', balance)

        foot = 'A' + str(row + 7) + ':' + 'H' + str(row + 7)
        sheet.set_row(row + 6, 35)
        sheet.merge_range(foot, data['user_name'] + ' ' + '-' + ' ' + data['current_date'], footer)

        workbook.close()
        output.seek(0)
        response.stream.write(output.read())
        output.close()
