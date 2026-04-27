{
    'name': 'POS Cash Drawer',
    'summary': """POS Cash Drawer""",
    'version': '14.0',
    'description': """POS Auto Cash Drawer""",
    'author': 'Catalist Divergent ERP',
    'company': 'Catalist Divergent ERP',
    'website': 'https://www.catalisterp.com/',
    'category': 'Point of Sale',
    'depends': ['base', 'point_of_sale'],
    'license': 'LGPL-3',
    'data': [
             'security/ir.model.access.csv',
             'security/security.xml',
             'views/pos_config.xml',
             'views/invoicing_config.xml',
             'views/assets.xml',
             'views/pos_payment_method_views.xml'
            ],
    "qweb": ["static/src/xml/reference_code.xml"],

    'images': [],
    'demo': [],
    'installable': True,
    'auto_install': False,

}
