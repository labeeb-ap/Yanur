# -*- coding: utf-8 -*-
{
    "name" : "POS Scrap Order",
    "version" : "14.1",
    "category" : "point_of_sale",
    "depends" : ['base','point_of_sale'],
    "author": "Catalist",
    'summary': 'Cancel the pos customer order and add to the scrap',
    "description": """Add customer order as scrap """,
    "website" : "http://catalist.catalisterp.in/",
    "data": [
        'views/pos_order_form.xml',
    ],
    'qweb': [],
    "auto_install": False,
    "installable": True,
}

