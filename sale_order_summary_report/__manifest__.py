{
    'name': 'event order summary report',
    'version': '1.1',
    'summary': 'summary report',
    'sequence': -100,
    'description': """event order summary report""",
    'category': 'productivity',
    'website': 'https://www.odoo.com/page/billing',
    'depends': ['sale'],
    'data': [
             'security/ir.model.access.csv',
             'wizard/event_summary.xml',
             'report/summary_report_pdf.xml',
             'report/summary_report_pdf_template.xml'
             ],
    'demo': [],
    'qweb': [],
    'installable': True,
    'application': True,
    'auto_install': False,
    'license': 'LGPL-3',
}
