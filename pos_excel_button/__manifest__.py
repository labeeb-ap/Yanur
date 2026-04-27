{
    'name': 'POS Sales Details Excel',
    'version': '14.0.1.0.0',
    'summary': 'Add Export Excel button in POS Sales Details wizard and Daily Sales Report menu',
    'depends': ['point_of_sale'],
    'data': [
        'security/ir.model.access.csv',
        'views/pos_daily_sales_wizard.xml',
        # 'views/pos_details_wizard_inherit.xml',
    ],
    'installable': True,
    'application': False,
}
