# -*- coding: utf-8 -*-
# Part of BrowseInfo. See LICENSE file for full copyright and licensing details.

{
    "name": "All in One POS Features in Odoo",
    "version": "14.0.1.0.0",
    "category": "Point of Sale",
    'summary': 'All in One POS Features in Odoo',
    "description": """ All in One POS Features in Odoo
	""",
    "author": "Divergent Catalist Pvt ltd",
    "depends": ['base', 'sale_management', 'account', 'point_of_sale'],
    "price": 99,
    "currency": 'EUR',
    "website": "",
    "data": [
        'security/ir.model.access.csv',
        'data/data.xml',
        'views/assets.xml',
        'views/pos_config_view.xml',
        'views/pos_order_view.xml',
        'views/account_view.xml',
        'views/pos_gift_coupon.xml',
        'views/report_pos_gift_coupon.xml',
    ],
    'qweb': [
        'static/src/xml/pos_orders_list.xml',
        'static/src/xml/reorder_reprint_return.xml',
        # 'static/src/xml/sale_orders.xml',
        'static/src/xml/pos_bag_charges.xml',
        # 'static/src/xml/item_count.xml',
        'static/src/xml/pos_discount.xml',
        # 'static/src/xml/pos_stock.xml',
        'static/src/xml/gift_coupon_voucher.xml',
        'static/src/xml/clear_input_search.xml',
    ],
    'demo': [
        'data/demo.xml',
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
}
