# -*- coding: utf-8 -*-
{
    'name': 'POS Order Synchronization (Community)',
    'version': '2.0.4',
    'author': 'Catalist',
    'summary': 'POS Order sync between Salesman and Cashier',
    'description': "Allow salesperson to only create draft order and send draft order to Cashier for payment",
    'category': 'Point Of Sale',
    'website': 'http://catalist.catalisterp.in/',
    'depends': ['base', 'point_of_sale', 'pos_manager_validation_mac5'],
    'images': [
        'static/description/main_screenshot.png',
    ],
    'data': [
        'views/pos_assets.xml',
        'views/point_of_sale.xml',
        'views/res_users_view.xml'
    ],
    'images': ['static/description/main_screenshot.png'],
    'qweb': [
        'static/src/xml/screens/ChromeWidgets/OrdersIconChrome.xml',
        'static/src/xml/screens/ProductScreen/ControlButtons/OrderScreenButton.xml',
        'static/src/xml/screens/ProductScreen/ProductScreen.xml',
        'static/src/xml/screens/OrderScreen/OrderScreen.xml',
        'static/src/xml/screens/OrderScreen/PopupProductLines.xml',
        'static/src/xml/Popups/CreateDraftOrderPopup.xml',
        'static/src/xml/Popups/ReOrderPopup.xml',
        'static/src/xml/Popups/AuthenticationPopup.xml',
        'static/src/xml/Chrome.xml',
        'static/src/xml/screens/ReceiptScreen/OrderReceipt.xml',
    ],
    'installable': True,
    'auto_install': False,
}
