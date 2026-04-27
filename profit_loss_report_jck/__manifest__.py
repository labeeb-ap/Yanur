{
'name': 'Profit And Loss Report',
'version': '1.1',
'summary': 'Profit And Loss Report',
'sequence': -100,
'description': """restuarent software""",
'category': 'registration',
'website': 'https://www.odoo.com/login registration',

'depends': ['base','sale'],
'data': [
       'security/ir.model.access.csv',
       'wizard/profit_loss_report.xml',

          ],
'demo': [],
'qweb': [],
'installable': True,
'application': True,
'auto_install': False,
'license': 'LGPL-3',
}