{
    'name': 'POS Custom Receipt',
    'summary': """POS Receipt""",
    'version': '14.0',
    'description': """POS Receipt""",
    'author': 'Catalist Divergent ERP',
    'company': 'Catalist Divergent ERP',
    'website': 'https://www.catalisterp.com/',
    'category': 'Point of Sale',
    'depends': ['base', 'point_of_sale'],
    'license': 'LGPL-3',
    'data': [
             # 'views/company.xml',
             'views/assets.xml'],
    'qweb': ['static/src/xml/pos_receipt_view.xml'],

    'images': [],
    'demo': [],
    'installable': True,
    'auto_install': False,

}
