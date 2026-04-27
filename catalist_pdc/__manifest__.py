# -*- coding: utf-8 -*-
{
    'name': "Catalist PDC",
    'version': '14.0.1.0.0',
    'category': 'Industries',

    'summary': """
     This module is used for PDC Management.
       """,

    'description': """
    Catalist PDC Management 
    """,

    'author': "Divergent Catalist",
    'website': "https://www.catalisterp.com",


    'depends': ['base', 'sale', 'sale_management', 'account'],

    'data': [
        'security/ir.model.access.csv',
        'data/cheque.xml',
        'views/pdc_view.xml',
        'wizard/account_select_wizard_view.xml',
        'data/mail_template.xml',
        'data/pdc_cron.xml',
    ],

    'installable': True,
    'application': True,
    'auto_install': False

}
