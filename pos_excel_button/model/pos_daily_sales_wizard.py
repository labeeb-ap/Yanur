from odoo import models, fields, api
import io
import base64
import xlsxwriter
from collections import defaultdict
import pytz


class PosDailySalesWizard(models.TransientModel):
    _name = "pos.daily.sales.wizard"
    _description = "POS Daily Sales Wizard"

    start_date = fields.Datetime(
        string="From Date",
        required=True,
        default=lambda self: fields.Datetime.now()

    )
    end_date = fields.Datetime(
        string="To Date",
        required=True,
        default=lambda self: fields.Datetime.now()
    )
    pos_config_ids = fields.Many2many(
        "pos.config",
        string="Point of Sale",
        domain=lambda self: [("company_id", "=", self.env.company.id)]
    )
    file_data = fields.Binary("Excel File", readonly=True)
    file_name = fields.Char("File Name", readonly=True)

    @api.model
    def default_get(self, fields_list):
        res = super().default_get(fields_list)
        configs = self.env["pos.config"].search([("company_id", "=", self.env.company.id)])
        res["pos_config_ids"] = configs.ids
        return res

    # def _to_utc_range(self):
    #     tz = pytz.timezone(self.env.user.tz or "UTC")
    #     start_local = self.start_date
    #     end_local = self.end_date
    #
    #     if start_local and start_local.tzinfo is None:
    #         start_local = tz.localize(start_local)
    #     if end_local and end_local.tzinfo is None:
    #         end_local = tz.localize(end_local)
    #
    #     return start_local.astimezone(pytz.utc), end_local.astimezone(pytz.utc), tz

    def action_export_excel(self):
        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output, {"in_memory": True})
        ws = workbook.add_worksheet("Daily Sales Report")

        # ---------- Formats ----------
        main_heading = workbook.add_format({
            "bold": True, "font_size": 18, "font_color": "black",
            "bg_color": "#D9D993", "align": "center", "valign": "vcenter"
        })
        sub_heading = workbook.add_format({
            "font_size": 12, "align": "center", "valign": "vcenter", "border": 1
        })
        header_fmt = workbook.add_format({
            "bold": True, "font_color": "white", "bg_color": "#D99393",
            "align": "center", "valign": "vcenter"
        })
        money_fmt = workbook.add_format({"num_format": "#,##0.00", "align": "right"})
        date_fmt = workbook.add_format({"num_format": "dd/mm/yyyy", "align": "center"})
        sum_label = workbook.add_format({"bold": True, "bg_color": "#FFD966", "align": "right"})
        sum_amt = workbook.add_format({
            "bold": True, "bg_color": "#FFD966",
            "num_format": "#,##0.00", "align": "right"
        })

        # ---------- Layout ----------
        ws.set_row(0, 30)
        ws.set_row(1, 20)
        ws.set_row(3, 20)
        ws.merge_range("A1:F1", "Yanur Restaurant - Daily Sales Report", main_heading)

        # ---------- Convert Wizard Time to IST ----------
        tz_utc = pytz.utc
        tz_ist = pytz.timezone("Asia/Kolkata")

        start_dt_ist = self.start_date.replace(tzinfo=tz_utc).astimezone(tz_ist)
        end_dt_ist = self.end_date.replace(tzinfo=tz_utc).astimezone(tz_ist)

        start_str = start_dt_ist.strftime("%d-%b-%Y %I:%M:%S %p")
        end_str = end_dt_ist.strftime("%d-%b-%Y %I:%M:%S %p")

        outlet_name = ", ".join(self.pos_config_ids.mapped("name")) if self.pos_config_ids else "All Outlets"

        # ---------- Heading Row with IST Time ----------
        ws.merge_range(
            "A2:F2",
            f"Outlet: {outlet_name} | From: {start_str}  To: {end_str}",
            sub_heading
        )

        headers = ["Date", "Cash", "Card", "Bank Transfer", "Discount", "Total Sales"]
        for c, h in enumerate(headers):
            ws.write(3, c, h, header_fmt)
            ws.set_column(c, c, 18)

        # ---------- Fetch Orders ----------
        domain = [
            ("date_order", ">=", self.start_date),
            ("date_order", "<=", self.end_date),
            ("state", "in", ["paid", "done", "invoiced"]),
            ("company_id", "=", self.env.company.id),
        ]
        if self.pos_config_ids:
            domain.append(("config_id", "in", self.pos_config_ids.ids))

        orders = self.env["pos.order"].search(domain)

        # ---------- Aggregate ----------
        daily = defaultdict(lambda: {"cash": 0.0, "card": 0.0, "bank": 0.0,
                                     "discount": 0.0, "total": 0.0})
        for order in orders:
            order_dt = order.date_order.replace(tzinfo=pytz.utc).astimezone(tz_ist).date()
            day_key = order_dt

            for pay in order.payment_ids:
                name = (pay.payment_method_id.name or "").strip().lower()
                if pay.payment_method_id.is_cash_count or name == "cash":
                    daily[day_key]["cash"] += pay.amount
                elif "bank transfer" in name:
                    daily[day_key]["bank"] += pay.amount
                elif "card" in name or "credit" in name or "debit" in name:
                    daily[day_key]["card"] += pay.amount
                else:
                    if "bank" in name or "transfer" in name:
                        daily[day_key]["bank"] += pay.amount
                    else:
                        daily[day_key]["card"] += pay.amount

            disc_prod = order.session_id.config_id.discount_product_id
            order_discount = 0.0
            for line in order.lines:
                if line.discount:
                    order_discount += (line.price_unit * line.qty) * (line.discount / 100.0)
                if disc_prod and line.product_id.id == disc_prod.id:
                    order_discount += abs(line.price_subtotal_incl)

            daily[day_key]["discount"] += order_discount
            daily[day_key]["total"] += order.amount_total

        # ---------- Write Rows ----------
        r = 4
        tot_cash = tot_card = tot_bank = tot_disc = tot_sales = 0.0
        for d, vals in sorted(daily.items()):
            ws.set_row(r, 18)
            ws.write_datetime(r, 0, fields.Date.to_date(d), date_fmt)
            ws.write(r, 1, vals["cash"], money_fmt)
            ws.write(r, 2, vals["card"], money_fmt)
            ws.write(r, 3, vals["bank"], money_fmt)
            ws.write(r, 4, vals["discount"], money_fmt)
            ws.write(r, 5, vals["total"], money_fmt)

            tot_cash += vals["cash"]
            tot_card += vals["card"]
            tot_bank += vals["bank"]
            tot_disc += vals["discount"]
            tot_sales += vals["total"]
            r += 1

        ws.set_row(r, 20)
        ws.write(r, 0, "TOTAL", sum_label)
        ws.write(r, 1, tot_cash, sum_amt)
        ws.write(r, 2, tot_card, sum_amt)
        ws.write(r, 3, tot_bank, sum_amt)
        ws.write(r, 4, tot_disc, sum_amt)
        ws.write(r, 5, tot_sales, sum_amt)

        workbook.close()
        output.seek(0)
        self.file_data = base64.b64encode(output.read())
        self.file_name = "POS_Daily_Sales_Report.xlsx"

        return {
            "type": "ir.actions.act_url",
            "url": f"/web/content/?model=pos.daily.sales.wizard&id={self.id}&field=file_data&filename_field=file_name&download=true",
            "target": "self",
        }

    class PosConfig(models.Model):
        _inherit = "pos.config"

        def name_get(self):
            """Show only the POS name without '(user)'."""
            return [(record.id, record.name) for record in self]
