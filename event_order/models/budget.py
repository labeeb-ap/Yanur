from odoo import models, fields,api
#

class Budgete(models.Model):
    _inherit = 'crossovered.budget.lines'


    event_type = fields.Many2one('event.type.sale', string='Event Type', default=None)
    analytic_group = fields.Many2one('account.analytic.group', string='Group', default=None,required=1)

    @api.onchange('analytic_account_id')
    def onchange_analytic_account_id(self):
        if self.analytic_account_id:
            if self.analytic_account_id.group_id:
                self.analytic_group = self.analytic_account_id.group_id










