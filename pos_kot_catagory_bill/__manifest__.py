# -*- coding: utf-8 -*-
{
    'name': 'POS KOT Category Order Print',
    'summary': "Allow to Print Orders In KOT without repetation as per Point of Sale Category",
    'description': "Allow to Print Orders In KOT without repetation as per Point of Sale Category",

    'author': 'iPredict IT Solutions Pvt. Ltd.',
    'website': 'http://ipredictitsolutions.com',
    "support": "ipredictitsolutions@gmail.com",

    'category': 'Point of Sale',
    'version': '14.0.0.1.3',
    'depends': ['pos_kot_bill'],

    'data': ['views/pos_view.xml'],
    'qweb': ['static/src/xml/pos.xml'],

    'license': "OPL-1",
    'price': 15,
    'currency': "EUR",

    'installable': True,
    'application': True,

    'images': ['static/description/main.png'],
    'live_test_url': 'https://youtu.be/vk4Oi6D6Vk0',
    'pre_init_hook': 'pre_init_check',
}
