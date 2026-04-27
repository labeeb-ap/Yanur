from odoo import models, fields, api, _


class EmployeeExitClearance(models.Model):
    _name = 'employee.exit.clearance'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _rec_name = 'reference'

    reference = fields.Char(string='Reference', required=True, copy=False, readonly=True,
                            default=lambda self: _('New'))

    user_id = fields.Many2one('res.users', string="User")
    employee_id = fields.Many2one('hr.employee', string="Employee")
    last_day = fields.Date(string="Last Day Of Employee")
    notice_period = fields.Char(string="Notice Period")
    reason = fields.Text(string="Reason")

    state = fields.Selection(
        [('in_progress', 'In Progress'), ('hold', 'On Hold'), ('approved', 'Approved'), ('reject', 'Rejected')],
        string='Status', default='in_progress', tracking=True)

    remarks = fields.Text(string="Remarks", tracking=True)

    resignation_id = fields.Many2one('hr.resignation', string="Resignation Request")
    resig_department_id = fields.Many2one('employee.resignation.department', string="Department")

    @api.model
    def create(self, vals):
        if vals.get('reference', _('New')) == _('New'):
            vals['reference'] = self.env['ir.sequence'].next_by_code('employee.exit.clearance.code') or _('New')
        res = super(EmployeeExitClearance, self).create(vals)
        return res

    def button_in_progress(self):
        self.state = 'in_progress'

    def button_on_hold(self):
        self.state = 'hold'

    def button_approve(self):
        self.state = 'approved'

    def button_reject(self):
        self.state = 'reject'
