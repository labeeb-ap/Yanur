# -*- coding: utf-8 -*-
{
    "name" : "Event Order",
    "version" : "14.1",
    "sequence":-1000000,
    "category" : "crm",
    "depends" : ['base','crm','sale', 'sale_crm','sale_management','account','contacts','purchase','stock','analytic','om_account_budget'],
    "author": "Catalist",
    'summary': "event order catering",
    "description": """event order catering""",
    "website" : "http://catalist.catalisterp.in/",
    "data": [
        'security/ir.model.access.csv',
        'security/security.xml',
        'wizard/multiple_product_sale_view.xml',

        'views/event_order_crm.xml',
        'views/event_order_form.xml',
        'views/event_type.xml',
        'views/analytic_account.xml',
        'views/budget.xml',
        'views/complimentory_order_lines.xml',

        'report/event_order_report.xml',
        'report/event_order_report_template.xml',
        'report/event_order_report_template_v2.xml'
    ],
    'qweb': [],
    "auto_install": False,
    "installable": True,
}

