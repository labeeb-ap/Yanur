from odoo import models, fields, api, _
from odoo.exceptions import Warning


class AccountAccount(models.Model):
    _inherit = 'account.account'

    comp_ids = fields.Many2many('res.company', string='Allowed Companies', store=True)

    def create_chart_of_company(self):
        res = self.comp_ids
        if res:
            record_check = self.env['account.account'].sudo().search(
                [('company_id', '=', self.company_id.id), ('code', '=', self.code),
                 ('company_id', '=', res.ids)])
            if record_check:
                list6 = []
                list9 = []
                for i in res:
                    record_set = self.env['account.account'].sudo().search(
                        [('company_id', '!=', self.company_id.id), ('code', '=', self.code),
                         ('company_id', '=', i.ids)])
                    for n in record_set:
                        list6.append(n.company_id.id)
                for m in res.ids:
                    if self.company_id.id != m:
                        list9.append(m)
                re = set(list9) - set(list6)
                for p in re:
                    move_id = self.env['account.account'].sudo().create({
                        'company_id': p,
                        'comp_ids': [(6, 0, self.comp_ids.ids)],
                        'code': self.code,
                        'name': self.name,
                        'control_code':self.control_code,
                        'user_type_id': self.user_type_id.id,
                        'group_id': self.group_id.id,
                        'currency_id': self.currency_id.id,
                        'deprecated': self.deprecated,
                        # 'tax_ids': [(6, 0, self.tax_ids.ids)],
                        'tag_ids': [(6, 0, self.tag_ids.ids)],
                        'allowed_journal_ids': [(6, 0, self.allowed_journal_ids.ids)]
                    })
                record_delete = self.env['account.account'].sudo().search(
                    [('company_id', '!=', self.company_id.id), ('code', '=', self.code),
                     ('company_id', '!=', res.ids)])
                record_delete.unlink()
            else:
                raise Warning(_("Please Select Your Own Company"))

        elif not res:
            ch = self.env['account.account'].sudo().search(
                [('code', '=', self.code), ('company_id', '!=', self.company_id.id)])
            list = []
            for i in ch:
                list.append(i.company_id.id)
            com = self.env['res.company'].sudo().search(
                [('id', '!=', self.company_id.id)])
            list1 = []
            for j in com:
                list1.append(j.id)
            res = set(list1) - set(list)
            for k in res:
                move = self.env['account.account'].sudo().create({
                    'company_id': k,
                    'code': self.code,
                    'name': self.name,
                    'user_type_id': self.user_type_id.id,
                    'group_id': self.group_id.id,
                    'control_code': self.control_code,
                    'currency_id': self.currency_id.id,
                    'deprecated': self.deprecated,
                    # 'tax_ids': [(6, 0, self.tax_ids.ids)],
                    'tag_ids': [(6, 0, self.tag_ids.ids)],
                    'allowed_journal_ids': [(6, 0, self.allowed_journal_ids.ids)]
                })
