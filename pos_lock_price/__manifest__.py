# -*- coding: utf-8 -*-

{
    'name': "POS Price Lock",
    'summary': """
        Lock change price in Point Of Sale""",
    'description': """
        This module add features to lock change price in Point Of Sale 
    """,
    'author': "Divergent Catalist",
    'website': "",
    'category': 'Point Of Sale',
    'version': '14.0.1.0',
    'website': "https://www.catalisterp.com",
    'images': ['static/description/banner.jpg'],
    'depends': ['base', 'point_of_sale'],
    'data': [
        'views/assets.xml',
        'views/pos_config_view.xml',
    ],
    'qweb': [
        'static/src/xml/NumpadWidget.xml',
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
}
