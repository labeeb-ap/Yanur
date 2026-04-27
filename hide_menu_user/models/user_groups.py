from odoo import models, fields, api, _
from odoo.exceptions import Warning


class UserGroupsUser(models.Model):
    _name = 'user.groups.user'

    name = fields.Char(string="Name")

    @api.model
    def create(self, vals):
        res = super(UserGroupsUser, self).create(vals)
        group = self.env['user.groups.user'].search([('name', '=', res.name)])
        if len(group) > 1:
            raise Warning(_("Already Created The User Group"))
        return res

    def write(self, vals):
        res = super(UserGroupsUser, self).write(vals)
        group = self.env['user.groups.user'].search([('name', '=', self.name)])
        if len(group) > 1:
            raise Warning(_("Already Created The User Group"))
        return res
