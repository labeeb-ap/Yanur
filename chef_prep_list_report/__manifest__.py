{
    'name': 'Chef Prep report',
    'version': '1.1',
    'summary': 'Culinary report',
    'sequence': -100,
    'description': """Chef's daily preparation report""",
    'category': 'productivity',
    'website': 'https://www.odoo.com/page/billing',
    'depends': ['sale'],
    'data': [
             'security/ir.model.access.csv',
             'wizard/culinary_quantity_views.xml',
             'report/culinary_report_pdf.xml',
             'report/culinary_report_template.xml'
             ],
    'demo': [],
    'qweb': [],
    'installable': True,
    'application': True,
    'auto_install': False,
    'license': 'LGPL-3',
}
