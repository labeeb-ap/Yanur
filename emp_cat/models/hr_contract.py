# -*- coding: utf-8 -*-
from odoo import models, fields, api, tools, _


class HrContract(models.Model):
    _inherit = 'hr.contract'

    partial_credit_account_id = fields.Many2one('account.account', string='Credit Account')
    partial_debit_account_id = fields.Many2one('account.account', string='Debit Account')
    pf_num = fields.Char(string='PF Number', store=True, compute='_compute_employee_code')
    esi_num = fields.Char(string='ESI Number', store=True, compute='_compute_employee_code')
    gmc_num = fields.Char(string='GMC Number', store=True, compute='_compute_employee_code')
    employee_code = fields.Char(string='Employee Code', store=True, compute='_compute_employee_code')
    professional_tax = fields.Float(string='Professional Tax')
    tax_professional = fields.Float(string='Professional Tax')
    medical_insurance = fields.Float(string='Medical Insurance')
    tds_percentage = fields.Float(string='TDS %')

    @api.depends('employee_id')
    def _compute_employee_code(self):
        for rec in self:
            rec.employee_code = rec.employee_id.employee_code if rec.employee_id.employee_code else ""
            rec.pf_num = rec.employee_id.pf_num if rec.employee_id.pf_num else ""
            rec.esi_num = rec.employee_id.esi_num if rec.employee_id.esi_num else ""
            rec.gmc_num = rec.employee_id.gmc_num if rec.employee_id.gmc_num else ""

