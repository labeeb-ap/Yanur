{
    'name': 'POS Cash Drawer Maneger Validation',
    'summary': """POS Cash Drawer Maneger Validation""",
    'version': '14.0',
    'description': """POS Auto Cash Drawer""",
    'author': 'Catalist Divergent ERP',
    'company': 'Catalist Divergent ERP',
    'website': 'https://www.catalisterp.com/',
    'category': 'Point of Sale',
    'depends': ['base', 'point_of_sale','pos_auto_cash_drawer'],
    'license': 'LGPL-3',
    'data': [
             'security/ir.model.access.csv',
             'data/sequence.xml',
             'views/cash_drawer_settings_views.xml',
             'views/assets.xml',
            ],
    "qweb": [
        "static/src/xml/cash_drawer_button.xml",
        "static/src/xml/inputpassword_popup.xml",
    ],

    'images': [],
    'demo': [],
    'installable': True,
    'auto_install': False,

}
