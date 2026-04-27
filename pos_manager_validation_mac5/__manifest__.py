{
    'name': 'POS Manager Validation (User)',
    'version': '14.1',
    'summary': """ pos manager validation based on manager pin  """,
    'description': """
The module checks the validation based on manager pin . we cab give validation for order deletion,Decrease Quantity,Payment,Global Discount,Order line deletion,discount application and price change
""",
    'category': 'Point of Sale',
    'author': 'Divergent Catalist pvt ltd',
    "website": "www.catalisterp.com/",
    'depends': ['point_of_sale', 'pos_discount'],
    'data': [
        'views/pos_manager_validation_templates.xml',
        'views/res_users_views.xml',
        'views/pos_config_views.xml',
    ],
    'demo': [],
    'qweb': [],
    'installable': True,
    'application': False,
    'auto_install': False,
    'images': ['static/description/pos_ui_validate.png'],
}
