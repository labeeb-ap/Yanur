# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
{
    'name': 'Cash Account Report',
    'version': '14.0.1.0.0',
    'summary': 'Print Cash Account Report Through Wizard',
    'author': 'Divergent Catalist ERP Solutions',
    'company': 'Divergent Catalist ERP Solutions',
    'maintainer': 'Divergent Catalist ERP Solutions',
    'sequence': 10,
    'description': """Print Cash Account Report Through Wizard,
        Filter Cash Account Report Details by Date, Account Head""",
    'category': 'Accounting',
    'website': 'https://www.catalisterp.com/',
    'depends': ['base', 'account', 'contacts'],
    'data': ['security/ir.model.access.csv',
             'wizard/cash_account.xml',
             'wizard/cash_account_all.xml',
             'report/cash_account_report.xml',
             'report/cash_account_report_temp.xml',
             'report/cash_ac_general_report_temp.xml'
             ],
    'demo': [],
    'qweb': [],
    'licenSe': 'LGPL-3',
    'installable': True,
    'application': True,
    'auto_install': False,
}
