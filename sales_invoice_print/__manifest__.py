# -*- coding: utf-8 -*-
{
    'name': 'Sales Invoice Print',
    'version': '14.0.1.0.0',
    'sequence': -1,
    'summary': """Sales Invoice Print""",
    'description': """Sales Invoice Print""",
    'author': 'Divergent Catalist ERP Solutions',
    'website': 'https://www.catalisterp.com/',
    'category': 'Accounting',
    'depends': ['account', 'sale', 'event_order'],
    'data': [
        'reports/invoice_pdf.xml',
        'reports/invoice_pdf_template.xml'
    ],
    'licenSe': 'LGPL-3',
    'installable': True,
    'application': True,
    'auto_install': False
}
