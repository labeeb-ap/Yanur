from odoo import models, fields
from datetime import date


class DayBookReportWizard(models.TransientModel):
    _name = "day.book.report.wizard"
    _description = "Day Book Report"

    date = fields.Date(string='Date', default=date.today())

    def action_print_report(self):
        if self.date:
            filter_cdtn = '''where  am.state = 'posted' and am.move_type in ('in_invoice', 'out_invoice', 'out_refund',
             'in_refund') and am.invoice_date = '%s'
                ''' % self.date
            entry_filter_cdtn = '''where  am.state = 'posted' and am.move_type = 'entry' and aj.type = 'general' and
             aml.date = '%s'
                            ''' % self.date
            payment_filter_cdtn = '''where  apm.state = 'posted' and apm.date = '%s'
                            ''' % self.date

        query = """select am.invoice_date as doc_date, am.name as doc_name, aj.type as doc_type, rp.name as doc_partner,
         am.amount_total as doc_amount, am.move_type as doc_move from account_move am
                    left join account_journal aj on aj.id = am.journal_id
                    left join res_partner rp on rp.id = am.partner_id %s""" % (
            filter_cdtn)

        entry_query = """select aml.date entry_date, aml.move_name entry_no, aj.type entry_type, rp.name entry_partner,
         aml.debit entry_debit, aml.credit entry_credit, aa.code aa_code, aa.name aa_name from account_move_line aml
                            left join account_move am on am.id = aml.move_id
                            left join account_journal aj on aj.id = aml.journal_id
                            left join res_partner rp on rp.id = aml.partner_id
							left join account_account aa on aa.id = aml.account_id %s""" % (
            entry_filter_cdtn)

        payment_query = """select apm.date payment_date, apm.name payment_no, aj.type payment_type,
         rp.name payment_partner, ap.amount payment_amount, ap.partner_type payment_partner_type from account_payment ap
                            left join account_move apm on apm.id = ap.move_id
                            left join account_journal aj on aj.id = apm.journal_id
                            left join res_partner rp on rp.id = ap.partner_id %s""" % (
            payment_filter_cdtn)

        self._cr.execute(payment_query)
        payment_day_book_ids = self._cr.dictfetchall()
        inv_payment = []
        for k in payment_day_book_ids:
            inv_payment.append({
                'payment_book_date': k['payment_date'].strftime("%d-%m-%Y"),
                'payment_book_no': k['payment_no'],
                'payment_book_type': k['payment_type'],
                'payment_book_partner': k['payment_partner'],
                'payment_book_amount': k['payment_amount'],
                'payment_book_partner_type': k['payment_partner_type'],
            })
        inv_payment.sort(key=lambda x: x['payment_book_no'])

        self._cr.execute(entry_query)
        entry_day_book_ids = self._cr.dictfetchall()
        inv_entry = []
        for j in entry_day_book_ids:
            inv_entry.append({
                'entry_book_date': j['entry_date'].strftime("%d-%m-%Y"),
                'entry_book_no': j['entry_no'],
                'entry_book_type': j['entry_type'],
                'entry_book_partner': j['entry_partner'],
                'entry_book_debit': j['entry_debit'],
                'entry_book_credit': j['entry_credit'],
                'entry_acc_code': j['aa_code'],
                'entry_acc_name': j['aa_name'],
            })
        inv_entry.sort(key=lambda x: x['entry_book_no'])

        self._cr.execute(query)
        day_book_ids = self._cr.dictfetchall()
        inv = []
        for i in day_book_ids:
            inv.append({
                'day_book_date': i['doc_date'].strftime("%d-%m-%Y"),
                'day_book_no': i['doc_name'],
                'day_book_type': i['doc_type'],
                'day_book_partner': i['doc_partner'],
                'day_book_amount': i['doc_amount'],
                'day_book_move': i['doc_move'],
            })
        inv.sort(key=lambda x: x['day_book_no'])

        data = {
            'ids': self.ids,
            'model': self._name,
            'date': self.date.strftime("%d-%m-%Y"),
            'val': inv,
            'entry': inv_entry,
            'payment': inv_payment,
        }
        action = self.env.ref('day_book_report.day_book_report_pdf').report_action(self, data=data)
        action.update({'close_on_report_download': True})
        return action
