# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
{
    'name': 'Inventory IN/OUT Report',
    'version': '14.1',
    'summary': 'Report of IN and OUT order of Inventory',
    'sequence': 1,
    'description': """Report of IN and OUT order of Inventory""",
    'category': 'Sales',
    "author": "Divergent Catalist pvt ltd",
    "website": "www.catalisterp.com/",
    'depends': ['stock', 'sale'],
    'data': [
        'security/ir.model.access.csv',
        'wizard/inventory_in_out_wizard.xml',
        'reports/inventory_in_out_pdf.xml',
        'reports/inventory_in_out_report_template.xml',

        # 'views/account_move.xml',
    ],
    'demo': [],
    'qweb': [],
    'installable': True,
    'application': True,
    'auto_install': False,
    'license': 'LGPL-3',
}
