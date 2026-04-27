from PIL.ImageChops import difference

from odoo import fields, models, _
from datetime import date
from odoo.exceptions import UserError


class ProfitLossReportWizard(models.TransientModel):
    _name = 'cash.flow.wizard'
    _description = 'Cash Flow Wizard'

    fileout = fields.Binary('File', readonly=True)
    fileout_filename = fields.Char('Filename', readonly=True)

    start_date = fields.Date(string='Start Date',  default=lambda self: date.today().replace(day=1))
    end_date = fields.Date(string='End Date', default=date.today())
    # company_ids = fields.Many2many('res.company', string="Company")
    # detailed_summary = fields.Boolean(string="Detailed Summary", store=True)
    analytic_account_ids=fields.Many2many('account.analytic.account',string='Analytic account')


    def cash_flow_get_values(self):
        # Your SQL with date filter



        if self.start_date > self.end_date:
            raise UserError(_("Start Date is GreaterThan End Date"))
        else:
            base_condition = """WHERE (aa.cash_flow IS NULL OR aa.cash_flow = false)
                AND aml.parent_state = 'posted' 
                AND aml.date BETWEEN '%s' AND '%s' """ % (self.start_date, self.end_date)

        if self.analytic_account_ids:
            if len(self.analytic_account_ids) == 1:
                analytic_id = str(self.analytic_account_ids.id)
                base_condition += f""" AND (
                    aml.analytic_distribution::text ILIKE '%"{analytic_id},%'
                    OR aml.analytic_distribution::text ILIKE '%,{analytic_id}"%'
                    OR aml.analytic_distribution::text ILIKE '%"{analytic_id}"%'
                ) """
                filter_cdtn = base_condition + " GROUP BY aa.name, aat.name ORDER BY aat.name "
            else:
                conditions = []
                for analytic_id in self.analytic_account_ids.ids:
                    id_str = str(analytic_id)
                    conditions.append(f"""aml.analytic_distribution::text ILIKE '%"{id_str},%'""")
                    conditions.append(f"""aml.analytic_distribution::text ILIKE '%,{id_str}"%'""")
                    conditions.append(f"""aml.analytic_distribution::text ILIKE '%"{id_str}"%'""")
                base_condition += " AND (" + " OR ".join(conditions) + ")"
                filter_cdtn = base_condition + " GROUP BY aa.name, aat.name ORDER BY aat.name "
        else:
            filter_cdtn = base_condition + " GROUP BY aa.name, aat.name ORDER BY aat.name "

        query = """
        SELECT
            aa.name AS account_head,      
            sum(aml.debit) AS debit,
            sum(aml.credit) AS credit,
			aat.name AS account_type
        FROM account_move_line aml
        JOIN account_account aa ON aml.account_id = aa.id
        JOIN account_move am ON aml.move_id = am.id
        JOIN account_account_type aat ON aa.user_type_id = aat.id
        INNER JOIN (
            SELECT am1.id 
            FROM account_move_line aml1
            JOIN account_account aa1 ON aml1.account_id = aa1.id
            JOIN account_move am1 ON aml1.move_id = am1.id
            WHERE aa1.cash_flow = TRUE AND aml1.parent_state = 'posted'
            group by am1.id
        ) AS amd ON am.id = amd.id
        %s
        """ % (filter_cdtn,)


        self.env.cr.execute(query)

        rows = self.env.cr.fetchall()

        # Convert into list of dicts for QWeb
        values = [{
            'debit': r[1],
            'credit': r[2],
            'account_head': r[0],
            'account_type':r[3]
        } for r in rows]

        return values

    def action_print_cash_flow(self):
        values = self.cash_flow_get_values()  # your query function

        account_types = list({v['account_type'] for v in values})


        total_debit = 0
        total_credit = 0
        for row in values:
            total_debit = total_debit + row['debit']
            total_credit = total_credit + row['credit']

        difference = total_credit - total_debit

        data = {
            'from_date': self.start_date.strftime('%d-%m-%Y'),
            'to_date': self.end_date.strftime('%d-%m-%Y'),
            'analytic_account_ids': ' , '.join(name.upper() for name in self.analytic_account_ids.mapped('name')),
            'difference': difference,
            'total_debit': total_debit,
            'total_credit': total_credit,
            'comp_name': self.env.company.name,
            'report_name': 'Cash Flow Statement',
            'values': values,
            'account': account_types,
        }
        return self.env.ref('cash_flow.cash_flow_report_pdf').report_action(self, data= data)
