# from typing import io
import io

from odoo import models, fields
import base64
from odoo.http import request
from odoo.tools import date_utils
from odoo.tools.safe_eval import json

try:
    from odoo.tools.misc import xlsxwriter
except ImportError:
    import xlsxwriter


class PartnerStatementReport(models.TransientModel):
    _name = 'partner.statement.report'
    _description = 'Partner Statement Report'

    partner_id = fields.Many2one('res.partner', string='Partner')
    from_date = fields.Date(string='From Date')
    to_date = fields.Date(string='To Date')
    account_type = fields.Selection([('credit', 'Supplier'), ('debit', 'Customer')], default='debit',
                                    string="Account Type")

    def print_xlsx_report(self):
        date_from = self.from_date.strftime('%Y-%m-%d')
        # date_from = self.from_date.strftime('%d-%m-%Y')
        date_to = self.to_date.strftime('%Y-%m-%d')
        acnt_type_str = self.account_type

        if acnt_type_str == 'debit':
            # self.env.cr.execute((""" select aml.date, am.name, am.move_type, aml.debit, aml.credit, aml.partner_id, account_account.name as account_name
            #     FROM account_move_line aml left join account_move am on aml.move_id = am.id left join account_account
            #     on aml.account_id=account_account.id where account_account.id in (7) and aml.partner_id = %s and am.date <= '%s'
            #                                     """) % (self.partner_id.id, date_to))

            # self.env.cr.execute((""" select aml.date, am.name, aml.name, am.move_type, aml.debit, aml.credit, aml.partner_id, account_account.name as account_name, account_journal.name as journal_name, aml.name as label
            # FROM account_move_line aml left join account_move am on aml.move_id = am.id left join account_account on aml.account_id = account_account.id
            # left join account_journal on aml.journal_id = account_journal.id where account_account.id in (7) and aml.partner_id = %s and am.date <= '%s'
            #                                     """) % (self.partner_id.id, date_to))

            self.env.cr.execute((""" select aml.date, am.name, aml.name, am.move_type, aml.debit, aml.credit, aml.partner_id, account_journal.type, account_account.name as account_name, account_journal.name as journal_name, aml.name as label, am.name as doc_name
                        FROM account_move_line aml left join account_move am on aml.move_id = am.id left join account_account on aml.account_id = account_account.id 
                        left join account_journal on aml.journal_id = account_journal.id where account_account.id in (7) and aml.partner_id = %s and am.date <= '%s'
                                                            """) % (self.partner_id.id, date_to))

        else:
            # self.env.cr.execute((""" select aml.date, am.name, am.move_type, aml.debit, aml.credit, aml.partner_id, account_account.name as account_name
            #                 FROM account_move_line aml left join account_move am on aml.move_id = am.id left join account_account
            #                 on aml.account_id=account_account.id where account_account.id in (26) and aml.partner_id = %s and am.date <= '%s'
            #                                                 """) % (self.partner_id.id, date_to))

            # self.env.cr.execute((""" select aml.date, am.name, am.move_type, aml.debit, aml.credit, aml.name, aml.partner_id, account_account.name as account_name, account_journal.name as journal_name, aml.name as label
            #             FROM account_move_line aml left join account_move am on aml.move_id = am.id left join account_account on aml.account_id = account_account.id
            #             left join account_journal on aml.journal_id = account_journal.id where account_account.id in (26) and aml.partner_id = %s and am.date <= '%s'
            #                                                 """) % (self.partner_id.id, date_to))

            self.env.cr.execute((""" select aml.date, am.name, am.move_type, aml.debit, aml.credit, aml.name, aml.partner_id,account_journal.type, account_account.name as account_name, account_journal.name as journal_name, aml.name as label, am.name as doc_name
                                    FROM account_move_line aml left join account_move am on aml.move_id = am.id left join account_account on aml.account_id = account_account.id 
                                    left join account_journal on aml.journal_id = account_journal.id where account_account.id in (26) and aml.partner_id = %s and am.date <= '%s'
                                                                        """) % (self.partner_id.id, date_to))

        acnt_move_ids = self.env.cr.dictfetchall()

        open_dr_sum = 0
        open_cr_sum = 0
        current_dr_sum = 0
        current_cr_sum = 0
        move_ids = []
        templist = []
        # acct_type_dict = {
        #                     'in_refund':'Debit Note',
        #                     'in_invoice':'Purchase Invoice',
        #                     'out_invoice':'Tax Invoice',
        #                     'out_refund':'Credit Note',
        #                     'entry':'Journal'
        #                     }

        for items in acnt_move_ids:
            # print("line_ids",items)
            items['date'] = items['date']
            all_date = items['date']
            if date_from >= str(all_date):
                # print(date_from, "hhhh---", str(all_date))
                open_dr_sum += items['debit']
                open_cr_sum += items['credit']
            else:
                current_dr_sum += items['debit']
                current_cr_sum += items['credit']
                # move_types = items['move_type']
                # if move_types in acct_type_dict.keys():
                #     items['move_type'] = acct_type_dict[move_types]

                templist.append(items)
                move_ids = sorted(templist, key=lambda d: d['date'])
            # print("type",items['type'])
            if items['type'] == "general":
                items['journal_name'] = items['label']
        if open_dr_sum >= open_cr_sum:
            open_bal_dr = open_dr_sum - open_cr_sum
            open_bal_cr = None
        else:
            open_bal_cr = open_cr_sum - open_dr_sum
            open_bal_dr = None

        if current_dr_sum >= current_cr_sum:
            bal_dr = current_dr_sum - current_cr_sum
            bal_cr = None
        else:
            bal_cr = current_cr_sum - current_dr_sum
            bal_dr = None

        data = {
            'from_date': self.from_date.strftime('%d-%b-%Y'),
            'to_date': self.to_date.strftime('%d-%b-%Y'),
            'open_bal_dr': open_bal_dr,
            'open_bal_cr': open_bal_cr,
            'current_dr_sum': current_dr_sum,
            'current_cr_sum': current_cr_sum,
            'bal_dr': bal_dr,
            'bal_cr': bal_cr,
            'partner_id': self.partner_id.name,
            'move_ids': move_ids
        }

        return {
            'type': 'ir.actions.report',
            'data': {'model': 'partner.statement.report',
                     'options': json.dumps(data, default=date_utils.json_default),
                     'output_format': 'xlsx',
                     'report_name': 'Partner Statement Report',
                     },
            'report_type': 'xlsx',
        }

    def get_xlsx_report(self, data, response):
        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})
        wizard_record = request.env['partner.statement.report'].search([])[-1]
        row = 4
        col = 0
        sheet = workbook.add_worksheet('Partner Statement Ageing')
        bold1 = workbook.add_format({'bold': True, 'align': 'center', 'bg_color': '#919191', 'border': 1})
        bold2 = workbook.add_format({'bold': True, 'align': 'center'})
        bold3 = workbook.add_format({'bold': True, 'align': 'left'})
        bold4 = workbook.add_format({'bold': True, 'bg_color': '#bfbbbd', 'align': 'left'})
        size = workbook.add_format({'font_size': 20, 'bg_color': '#c7c5c6', 'align': 'center', 'border': 1})
        rowss = sheet.set_default_row(20)
        align_data_center = workbook.add_format({'align': 'center', 'valign': 'vcenter'})
        align_data_right = workbook.add_format({'align': 'right', 'valign': 'vcenter'})

        sheet.merge_range('B3:C3', 'Date From :' + data['from_date'], bold2)
        sheet.write(row - 2, col + 2, 'Date To :' + data['to_date'], bold2)
        sheet.merge_range('E3:G3', 'Partner   :' + data['partner_id'], bold2)
        sheet.merge_range('B1:G1', 'Partner Statement Ageing Report', size)
        sheet.write(row, col + 1, 'Sl_no', bold1)
        sheet.write(row, col + 2, 'Date', bold1)
        sheet.write(row, col + 3, 'Doc no', bold1)
        sheet.write(row, col + 4, 'Doc Type ', bold1)
        sheet.write(row, col + 5, 'Dr', bold1)
        sheet.write(row, col + 6, 'Cr', bold1)

        current_print = 'B' + str(row + 2) + ':' + 'G' + str(row + 2)
        # sheet.set_row(row1 + 2, 20)
        if data['open_bal_dr']:
            sheet.merge_range(current_print, 'Opening Balance' + '  ' + str(data['open_bal_dr']) + ' Dr')
        elif data['open_bal_cr']:
            sheet.merge_range(current_print, 'Opening Balance' + '  ' + str(data['open_bal_cr']) + ' Cr')
        # sheet.write(row + 1, col + 3, 'Opening Balance', align)
        # sheet.write(row + 1, col + 4, data['open_bal_dr'], align)
        # sheet.write(row + 1, col + 5, data['open_bal_cr'], align)

        sheet.set_column('A:A', 10)
        sheet.set_column('B:B', 25)
        sheet.set_column('C:C', 30)
        sheet.set_column('D:D', 30)
        sheet.set_column('E:E', 20)
        sheet.set_column('F:F', 20)

        row += 2
        sl_no = 0
        for i in data['move_ids']:
            sl_no += 1
            sheet.write(row, col + 1, sl_no, align_data_center)
            sheet.write(row, col + 2, i['date'], align_data_center)
            sheet.write(row, col + 3, ' ' + i['doc_name'])
            if i['journal_name']:
                sheet.write(row, col + 4, ' ' + str(i['journal_name']))
            sheet.write(row, col + 5, str(i['debit']) + ' ', align_data_right)
            sheet.write(row, col + 6, str(i['credit']) + ' ', align_data_right)
            row += 1

        sheet.write(row + 1, col + 3, 'Total :', bold2)
        sheet.write(row + 1, col + 4, data['current_dr_sum'], align_data_right)
        sheet.write(row + 1, col + 5, data['current_cr_sum'], align_data_right)
        #
        sheet.write(row + 3, col + 3, 'Balance :', bold2)
        sheet.write(row + 3, col + 4, data['bal_dr'], align_data_right)
        sheet.write(row + 3, col + 5, data['bal_cr'], align_data_right)

        workbook.close()
        output.seek(0)
        response.stream.write(output.read())
        output.close()

    def print_pdf_report(self):
        date_from = self.from_date.strftime('%Y-%m-%d')
        date_to = self.to_date.strftime('%Y-%m-%d')
        acnt_type_str = self.account_type

        if acnt_type_str == 'debit':
            # self.env.cr.execute((""" select aml.date, am.name, am.move_type, aml.debit, aml.credit, aml.partner_id, account_account.name as account_name
            #     FROM account_move_line aml left join account_move am on aml.move_id = am.id left join account_account
            #     on aml.account_id=account_account.id where account_account.id in (7) and aml.partner_id = %s and am.date <= '%s'
            #                                     """) % (self.partner_id.id, date_to))

            self.env.cr.execute((""" select aml.date, am.name, aml.name, am.move_type, aml.debit, aml.credit, aml.partner_id, account_journal.type, account_account.name as account_name, account_journal.name as journal_name, aml.name as label, am.name as doc_name
                        FROM account_move_line aml left join account_move am on aml.move_id = am.id left join account_account on aml.account_id = account_account.id 
                        left join account_journal on aml.journal_id = account_journal.id where account_account.id in (7) and aml.partner_id = %s and am.date <= '%s'
                                                """) % (self.partner_id.id, date_to))

        else:
            # self.env.cr.execute((""" select aml.date, am.name, am.move_type, aml.debit, aml.credit, aml.partner_id, account_account.name as account_name
            #                 FROM account_move_line aml left join account_move am on aml.move_id = am.id left join account_account
            #                 on aml.account_id=account_account.id where account_account.id in (26) and aml.partner_id = %s and am.date <= '%s'
            #                                                 """) % (self.partner_id.id, date_to))

            self.env.cr.execute((""" select aml.date, am.name, am.move_type, aml.debit, aml.credit, aml.name, aml.partner_id,account_journal.type, account_account.name as account_name, account_journal.name as journal_name, aml.name as label, am.name as doc_name
                                    FROM account_move_line aml left join account_move am on aml.move_id = am.id left join account_account on aml.account_id = account_account.id 
                                    left join account_journal on aml.journal_id = account_journal.id where account_account.id in (26) and aml.partner_id = %s and am.date <= '%s'
                                                            """) % (self.partner_id.id, date_to))

        acnt_move_ids = self.env.cr.dictfetchall()
        open_dr_sum = 0
        open_cr_sum = 0
        current_dr_sum = 0
        current_cr_sum = 0
        templist = []
        move_ids = []
        # acct_type_dict = {
        #     'in_refund': 'Debit Note',
        #     'in_invoice': 'Purchase Invoice',
        #     'out_invoice': 'Tax Invoice',
        #     'out_refund': 'Credit Note',
        #     'entry': 'Journal'
        # }

        for items in acnt_move_ids:
            items['date'] = items['date'].strftime('%d-%m-%Y')
            all_date = items['date']
            if date_from >= str(all_date):
                open_dr_sum += items['debit']
                open_cr_sum += items['credit']
            else:
                current_dr_sum += items['debit']
                current_cr_sum += items['credit']
                # move_types = items['move_type']
                # if move_types in acct_type_dict.keys():
                #     items['move_type'] = acct_type_dict[move_types]
                templist.append(items)
                move_ids = sorted(templist, key=lambda d: d['date'])
            if items['type'] == "general":
                items['journal_name'] = items['label']
        if open_dr_sum >= open_cr_sum:
            open_bal_dr = open_dr_sum - open_cr_sum
            open_bal_cr = None
        else:
            open_bal_cr = open_cr_sum - open_dr_sum
            open_bal_dr = None

        if current_dr_sum >= current_cr_sum:
            bal_dr = current_dr_sum - current_cr_sum
            bal_cr = None
        else:
            bal_cr = current_cr_sum - current_dr_sum
            bal_dr = None

        data = {
            'from_date': self.from_date.strftime('%d-%b-%Y'),
            'to_date': self.to_date.strftime('%d-%b-%Y'),
            'open_bal_dr': open_bal_dr,
            'open_bal_cr': open_bal_cr,
            'current_dr_sum': current_dr_sum,
            'current_cr_sum': current_cr_sum,
            'bal_dr': bal_dr,
            'bal_cr': bal_cr,
            'partner_id': self.partner_id.name,
            'move_ids': move_ids,

            'company_name': self.env.company.name,
            'com_street': self.env.company.street,
            'com_street2': self.env.company.street2,
            'com_city': self.env.company.city,
            'com_state': self.env.company.state_id.name,
            'com_zip': self.env.company.zip,
            'com_country': self.env.company.country_id.name,
            'com_phone': self.env.company.phone,
            'com_email': self.env.company.email

        }

        return self.env.ref('partner_statement_report.partner_statement_report_pdf_print').report_action(self,
                                                                                                         data=data)

    def mail_report(self):
        date_from = self.from_date.strftime('%Y-%m-%d')
        date_to = self.to_date.strftime('%Y-%m-%d')
        acnt_type_str = self.account_type

        if acnt_type_str == 'debit':
            # self.env.cr.execute((""" select aml.date, am.name, am.move_type, aml.debit, aml.credit, aml.partner_id, account_account.name as account_name
            #     FROM account_move_line aml left join account_move am on aml.move_id = am.id left join account_account
            #     on aml.account_id=account_account.id where account_account.id in (7) and aml.partner_id = %s and am.date <= '%s'
            #                                     """) % (self.partner_id.id, date_to))

            self.env.cr.execute((""" select aml.date, am.name, aml.name, am.move_type, aml.debit, aml.credit, aml.partner_id, account_journal.type, account_account.name as account_name, account_journal.name as journal_name, aml.name as label, am.name as doc_name
                                    FROM account_move_line aml left join account_move am on aml.move_id = am.id left join account_account on aml.account_id = account_account.id 
                                    left join account_journal on aml.journal_id = account_journal.id where account_account.id in (7) and aml.partner_id = %s and am.date <= '%s'
                                                            """) % (self.partner_id.id, date_to))

        else:
            # self.env.cr.execute((""" select aml.date, am.name, am.move_type, aml.debit, aml.credit, aml.partner_id, account_account.name as account_name
            #                 FROM account_move_line aml left join account_move am on aml.move_id = am.id left join account_account
            #                 on aml.account_id=account_account.id where account_account.id in (26) and aml.partner_id = %s and am.date <= '%s'
            #                                                 """) % (self.partner_id.id, date_to))

            self.env.cr.execute((""" select aml.date, am.name, am.move_type, aml.debit, aml.credit, aml.name, aml.partner_id,account_journal.type, account_account.name as account_name, account_journal.name as journal_name, aml.name as label, am.name as doc_name
                                                FROM account_move_line aml left join account_move am on aml.move_id = am.id left join account_account on aml.account_id = account_account.id 
                                                left join account_journal on aml.journal_id = account_journal.id where account_account.id in (26) and aml.partner_id = %s and am.date <= '%s'
                                                                        """) % (self.partner_id.id, date_to))

        acnt_move_ids = self.env.cr.dictfetchall()
        open_dr_sum = 0
        open_cr_sum = 0
        current_dr_sum = 0
        current_cr_sum = 0
        templist = []
        move_ids = []
        # acct_type_dict = {
        #     'in_refund': 'Debit Note',
        #     'in_invoice': 'Purchase Invoice',
        #     'out_invoice': 'Tax Invoice',
        #     'out_refund': 'Credit Note',
        #     'entry': 'Journal'
        # }

        for items in acnt_move_ids:
            items['date'] = items['date'].strftime('%d-%m-%Y')
            all_date = items['date']
            if date_from >= str(all_date):
                open_dr_sum += items['debit']
                open_cr_sum += items['credit']
            else:
                current_dr_sum += items['debit']
                current_cr_sum += items['credit']
                # move_types = items['move_type']
                # if move_types in acct_type_dict.keys():
                #     items['move_type'] = acct_type_dict[move_types]
                templist.append(items)
                move_ids = sorted(templist, key=lambda d: d['date'])
            if items['type'] == "general":
                items['journal_name'] = items['label']
        if open_dr_sum >= open_cr_sum:
            open_bal_dr = open_dr_sum - open_cr_sum
            open_bal_cr = None
        else:
            open_bal_cr = open_cr_sum - open_dr_sum
            open_bal_dr = None

        if current_dr_sum >= current_cr_sum:
            bal_dr = current_dr_sum - current_cr_sum
            bal_cr = None
        else:
            bal_cr = current_cr_sum - current_dr_sum
            bal_dr = None

        data = {
            'from_date': self.from_date.strftime('%d-%b-%Y'),
            'to_date': self.to_date.strftime('%d-%b-%Y'),
            'open_bal_dr': open_bal_dr,
            'open_bal_cr': open_bal_cr,
            'current_dr_sum': current_dr_sum,
            'current_cr_sum': current_cr_sum,
            'bal_dr': bal_dr,
            'bal_cr': bal_cr,
            'partner_id': self.partner_id.name,
            'move_ids': move_ids
        }

        report_template_id = self.env.ref(
            'partner_statement_report.partner_statement_report_pdf_print').sudo()._render_qweb_pdf(self.id, data)
        data_record = base64.b64encode(report_template_id[0])
        ir_values = {
            'name': "Partner statement report",
            'type': 'binary',
            'datas': data_record,
            'store_fname': data_record,
            'mimetype': 'application/x-pdf',
        }
        data_id = self.env['ir.attachment'].create(ir_values)
        template = self.env['mail.template'].search([('id', '=', 1)])

        template.attachment_ids = [(6, 0, [data_id.id])]
        email_values = {'email_to': self.partner_id.email,
                        'subject': 'Partner Statement Report',
                        'email_from': self.env.user.email}
        template.send_mail(self.id, email_values=email_values, force_send=True)
        template.attachment_ids = [(3, data_id.id)]
        return True
