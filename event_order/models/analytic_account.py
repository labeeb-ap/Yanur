from odoo import models, fields,api
#

class AnalyticAccount(models.Model):
    _inherit = 'account.analytic.account'

    sale_profit = fields.Selection([('company', 'Company'),
                                   ('management', 'Management'),
                                   ('both', 'Company / Management'),
                                   ], default="", string="P and L Type")

    company_id = fields.Many2one('res.company', string='Company', default=None)
    sale = fields.Boolean(string='Is Income')
    royalty = fields.Boolean(string='Royalty')

class AnalyticHideGroup(models.Model):
    _inherit = 'account.analytic.group'

    company_id = fields.Many2one('res.company', string='Company', default=None)










