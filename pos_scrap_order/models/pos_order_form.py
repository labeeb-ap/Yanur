from odoo import models, fields, api, _

class StockScrap(models.Model):
    _inherit = 'stock.scrap'

    feedback = fields.Text(string="Feedback")

    @api.model
    def action_scrap_order(self, vals):
        product = self.env['product.product'].search([('id', '=', vals['product_id'])])
        product_template = product.product_tmpl_id
        scrap = self.env['stock.scrap'].create({
                    'product_id': vals['product_id'],
                    'scrap_qty': abs( vals['scrap_qty']),
                    'feedback': vals['origin'],
                    'product_uom_id': product_template.uom_id.id,
                })

        return True
