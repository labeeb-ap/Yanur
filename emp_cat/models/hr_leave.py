# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class HolidaysType(models.Model):
    _inherit = "hr.leave.type"

    type_of_leave = fields.Selection([('casual', 'Casual'), ('sick', 'Sick')],default='casual', string="Leave Type")
    is_paid_time_off = fields.Boolean(string='Paid Time Off')
    is_unpaid_time_off = fields.Boolean(string='Unpaid Time Off')


class Holidays(models.Model):
    _inherit = "hr.leave"

    @api.onchange('holiday_status_id')
    def _onchange_holiday_status_id(self):
        for rec in self:
            if rec.holiday_status_id:
                rec.type_of_leave = rec.holiday_status_id.type_of_leave

    type_of_leave = fields.Selection([('casual', 'Casual'), ('sick', 'Sick')], default='casual', string="Leave Type")


