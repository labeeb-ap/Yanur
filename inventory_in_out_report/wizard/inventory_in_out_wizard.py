import io
from datetime import datetime

from odoo import models, fields, _


class InventoryInOutReportWizard(models.TransientModel):
    _name = "inventory.in.out.report.wizard"
    _description = "Inventory In Out Report"

    fr_date = fields.Date(string='From Date')
    to_date = fields.Date(string='To Date')
    item_name = fields.Many2one('product.product', string='Item')
    location_id = fields.Many2one('stock.location', string='Location')

    def action_opening_balance(self, to_date, fr_date, location, item_name):
        condition = ''
        if to_date and fr_date:
            x = fr_date.strftime('%Y-%m-%d 0:0:0')
            y = to_date.strftime('%Y-%m-%d 23:59:59')
            condition += """and sml.date <= '%s'""" % x
        if location:
            condition += ''' and (sml.location_id = %s or sml.location_dest_id = %s)''' % (
                self.location_id.id, self.location_id.id)
        if item_name:
            condition += """ and sml.product_id = %s""" % item_name.id
        self.env.cr.execute(("""SELECT sml.qty_done, sml.date, sml.product_id, sml.location_id, sml.location_dest_id
                                FROM stock_move_line as sml
                                where sml.state = 'done'
                                %s """)
                            % (condition))
        move_ids = self.env.cr.dictfetchall()
        opening_balance = 0
        for i in move_ids:
            if i['location_id'] == self.location_id.id:
                opening_balance -= i['qty_done']
            if i['location_dest_id'] == self.location_id.id:
                opening_balance += i['qty_done']
        return opening_balance

    def action_print_report(self):
        opening = self.action_opening_balance(to_date=self.to_date, fr_date=self.fr_date, location=self.location_id, item_name=self.item_name)
        print(opening)
        opening_bal = opening
        condition = ''
        if self.to_date and self.fr_date:
            date_to = self.to_date
            date_from = self.fr_date
            x = date_from.strftime('%Y-%m-%d 0:0:0')
            y = date_to.strftime('%Y-%m-%d 23:59:59')
            condition += """and sml.date between '%s' and '%s'""" % (x, y)
        if self.location_id:
            condition += ''' and (sml.location_id = %s or sml.location_dest_id = %s)''' % (
                self.location_id.id, self.location_id.id)
        if self.item_name:
            condition += """ and sml.product_id = %s""" % self.item_name.id
        self.env.cr.execute(("""SELECT sml.date, sml.reference as number, rp.name as description, sml.product_id, sml.location_id, sl.complete_name as loc_name,
                                        sml.location_dest_id, slo.complete_name as lo_dest_name,sml.qty_done, sml.state
                                        FROM stock_move_line as sml
                                        left join product_product as pp on sml.product_id = pp.id
                                        left join product_template as pt on pp.product_tmpl_id = pt.id
                                        left join stock_picking as sp on sml.picking_id = sp.id
                                        left join res_partner as rp on sp.partner_id = rp.id
                                        left join stock_location sl on sml.location_id = sl.id
                                        left join stock_location slo on sml.location_dest_id = slo.id
                                        where sml.state = 'done' 
                                        %s """)
                            % (condition))
        move_ids = self.env.cr.dictfetchall()
        for i in move_ids:
            tran = self.env['stock.picking'].search([('name', '=', i['number'])])
            if tran:
                i['trans'] = tran.picking_type_id.name
            else:
                i['trans'] = False
            i['dates'] = i['date'].strftime('%d-%m-%Y')
            if i['location_id'] == self.location_id.id:
                i['movement'] = "OUT"
                opening_bal -= i['qty_done']
                i['opening_qty_done'] = opening_bal
            if i['location_dest_id'] == self.location_id.id:
                i['movement'] = "IN"
                opening_bal += i['qty_done']
                i['opening_qty_done'] = opening_bal

        data = {
            'ids': self.ids,
            'model': self._name,
            'report_date': datetime.today(),
            'company_name': self.env.company.name,
            'com_street': self.env.company.street,
            'com_street2': self.env.company.street2,
            'com_city': self.env.company.city,
            'com_state': self.env.company.state_id.name,
            'com_zip': self.env.company.zip,
            'com_country': self.env.company.country_id.name,
            'com_phone': self.env.company.phone,
            'com_email': self.env.company.email,
            'from_date': self.fr_date,
            'to_dt': self.to_date,
            'it_name': self.item_name.name,
            'item_cd': self.item_name.id,
            'prod_qty': self.item_name.uom_id.name,
            'avg_price': self.item_name.lst_price,
            'sel_price': self.item_name.standard_price,
            'location_id': self.location_id.id,
            'opening': opening,
            'vals': move_ids,
        }
        action = self.env.ref('inventory_in_out_report.record_inventory_in_out_report_print').report_action(self,
                                                                                                            data=data)
        return action
