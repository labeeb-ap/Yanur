# -*- coding: utf-8 -*-
{
    'name': 'POS KOT Order Print',
    'summary': 'Allow to Print Orders In KOT without repetation',
    'description': """Module Developed for Print POS Orders for KOT.""",

    'author': 'iPredict IT Solutions Pvt. Ltd.',
    'website': 'http://ipredictitsolutions.com',
    "support": "ipredictitsolutions@gmail.com",

    'category': 'Point of Sale',
    'version': '14.0.0.1.3',
    'depends': ['pos_restaurant','point_of_sale'],

    'data': [
        'security/ir.model.access.csv',
        'security/security.xml',
        'data/sequence.xml',
        'views/pos_printer.xml',
        'views/kot_canceled_orderline_views.xml',
        'views/templates.xml',
        'views/pos_config.xml',
    ],
    'qweb': [
        'static/src/xml/preprintbill.xml',
        'static/src/xml/cancel_reason_popup.xml',
    ],

    'license': "OPL-1",
    'price': 50,
    'currency': "EUR",

    "auto_install": False,
    "installable": True,

    'images': ['static/description/banner.png'],
    'live_test_url': 'https://youtu.be/nRNIhj34Yj0',
    'pre_init_hook': 'pre_init_check',
}
