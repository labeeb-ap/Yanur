# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
{
    'name': 'Cash Flow',
    'version': '14.0',
    'summary': 'Cash Flow(PDF & Excel) Through Wizard',
    'author': 'Divergent Catalist ERP Solutions',
    'company': 'Divergent Catalist ERP Solutions',
    'maintainer': 'Divergent Catalist ERP Solutions',
    'description': """Print Cash Flow,
        Filter Report Details by Date, Account Head,....""",
    'category': 'Accounting',
    'website': 'https://www.catalisterp.com/',
    'depends': ['base', 'account', 'contacts','web'],
    # 'tb_report'
    'data': [
        'security/ir.model.access.csv',
        'views/account_field_view.xml',
        'wizard/cash_flow_wizard_view.xml',
        'report/report.xml',
        'report/cash_flow_report_temp.xml',
    ],
    'demo': [],
    'qweb': [],
    'licenSe': 'LGPL-3',
    'installable': True,
    'application': False,
    'auto_install': False,
}
