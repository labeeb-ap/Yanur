# -*- coding: utf-8 -*-
import psycopg2

from odoo import api, fields, models, _, tools

import logging

_logger = logging.getLogger(__name__)


class PosConfig(models.Model):
    _inherit = "pos.config"

    enable_order_sync = fields.Boolean("Order Sync")
    enable_operation_restrict = fields.Boolean("Operation Restrict")
    pos_managers_ids = fields.Many2many('res.users', 'pos_config_partner_rel', 'location_id', 'partner_id',
                                        string='Managers(Order Sync)')


class PosOrder(models.Model):
    _inherit = "pos.order"

    salesman_id = fields.Many2one('res.users', string='Salesman')

    def _order_fields(self, ui_order):
        res = super(PosOrder, self)._order_fields(ui_order)
        res.update({
            'salesman_id': ui_order.get('salesman_id') or False,
            'user_id': ui_order['cashier_id'] or False,
        })
        return res

    def _process_order(self, order, draft, existing_order):
        """Create or update an pos.order from a given dictionary.

        :param dict order: dictionary representing the order.
        :param bool draft: Indicate that the pos_order is not validated yet.
        :param existing_order: order to be updated or False.
        :type existing_order: pos.order.
        :returns: id of created/updated pos.order
        :rtype: int
        """
        order = order['data']
        pos_session = self.env['pos.session'].browse(order['pos_session_id'])
        if pos_session.state == 'closing_control' or pos_session.state == 'closed':
            order['pos_session_id'] = self._get_valid_session(order).id

        pos_order = False
        if not existing_order:
            pos_order = self.create(self._order_fields(order))
        else:
            pos_order = existing_order
            pos_order.lines.unlink()
            order['user_id'] = pos_order.user_id.id
            pos_order.write(self._order_fields(order))

        pos_order = pos_order.with_company(pos_order.company_id)
        self = self.with_company(pos_order.company_id)
        self._process_payment_lines(order, pos_order, pos_session, draft)

        if not draft:
            try:
                pos_order.action_pos_order_paid()
            except psycopg2.DatabaseError:
                # do not hide transactional errors, the order(s) won't be saved!
                raise
            except Exception as e:
                _logger.error('Could not fully process the POS Order: %s', tools.ustr(e))

        if self.env.user.pos_user_type == 'cashier':
            pos_order._create_order_picking()
        # pos_order._create_order_picking()

        if pos_order.to_invoice and pos_order.state == 'paid':
            pos_order.action_pos_order_invoice()

        return pos_order.id

    def unlink(self):
        cashier = self.env['res.users'].search([('sales_persons', 'in', [self.salesman_id.id])]).ids
        cashier.append(self.salesman_id.id)
        for user in cashier:
            session = self.env['pos.session'].search([('user_id', '=', user)], limit=1)
            if session:
                self.env['bus.bus'].sendmany([[(self._cr.dbname, 'order.sync', user),
                                               {'cancelled_order': self.read()}]])
        return super(PosOrder, self).unlink()

    def write(self, vals):
        for order in self:
            if order.name == '/':
                vals['name'] = order.config_id.sequence_id._next()
        res = super(PosOrder, self).write(vals)
        if len(self) == 1:
            cashier = self.env['res.users'].search([('sales_persons', 'in', [self.salesman_id.id])]).ids
            cashier.append(self.salesman_id.id)

            for user in cashier:
                session = self.env['pos.session'].search([('user_id', '=', user)], limit=1)
                if session:
                    self.env['bus.bus'].sendmany([[(self._cr.dbname, 'order.sync', user),
                                                   {'new_pos_order': self.read()}]])
        return res
