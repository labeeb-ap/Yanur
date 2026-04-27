# -*- coding: utf-8 -*-

{
    'name': 'Odoo 14 Payment Matching',
    'version': '14.0.1.0.0',
    'category': 'Accounting',
    'summary': """ Payment Matching""",
    'description': """
                    Payment Matching
                    """,
    'author': 'Catalist',
    'website': "https://www.catalisterp.com",
    'company': 'Catalist',
    'maintainer': 'Catalist',
    'depends': ['base', 'account', 'sale',],
    'data': [
            'views/payment_matching.xml',
            'views/assets.xml',
    ],
    'qweb': [
        'static/src/xml/template.xml',
        'static/src/xml/payment_matching.xml'
    ],
    'license': 'LGPL-3',
    'images': ['static/description/banner.gif'],
    'installable': True,
    'auto_install': False,
    'application': True,
}
