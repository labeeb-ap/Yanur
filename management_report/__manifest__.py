{
'name': 'MGT Budget Report',
'version': '1.1',
'summary': 'MGT Budget Report',
'sequence': -101,
'description': """restuarent software""",
'category': 'registration',
'website': 'https://www.odoo.com/login registration',

'depends': ['base','account'],
'data': [
       'security/ir.model.access.csv',
       'wizard/management_report.xml',
          ],
'demo': [],
'qweb': [],
'installable': True,
'application': True,
'auto_install': False,
'license': 'LGPL-3',
}