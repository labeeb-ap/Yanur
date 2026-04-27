{
'name': 'Daily Sales Report',
'version': '1.1',
'summary': 'daily sales report',
'sequence': -100,
'description': """restuarent software""",
'category': 'registration',
'website': 'https://www.odoo.com/login registration',

'depends': ['base','sale'],
'data': [
       'security/ir.model.access.csv',
       'wizard/daily_sales_wizard.xml',
          ],
'demo': [],
'qweb': [],
'installable': True,
'application': True,
'auto_install': False,
'license': 'LGPL-3',
}