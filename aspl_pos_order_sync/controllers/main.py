# -*- coding: utf-8 -*-
from odoo.http import request
from odoo.addons.bus.controllers.main import BusController


class OrderSyncController(BusController):

    def _poll(self, dbname, channels, last, options):
        """Add the relevant channels to the BusController polling."""
        if options.get('order.sync'):
            channels = list(channels)
            lock_channel = (
                request.db,
                'order.sync',
                options.get('order.sync')
            )
            channels.append(lock_channel)
        return super(OrderSyncController, self)._poll(dbname, channels, last, options)

