{
    'name': 'Pos Counter Closing',
    'version': '14.0.1.0.0',
    'summary': """Point Of Sale Counter Closing""",
    'description': """Point Of Sale Counter Closing""",
    'category': 'Point of Sale',
    'author': 'Divergent Catalist pvt ltd',
    'website': "https://www.catalisterp.com",
    'depends': [
        'sale', 'point_of_sale', 'pos_sale'
    ],
    'data': [
        'security/security.xml',
        'security/record_rules.xml',
        'security/ir.model.access.csv',
        # 'data/currency_type.xml',
        'views/currency_type_form.xml',
        'views/account_account_move.xml',
        'views/pos_payment_method_view.xml',
        'views/pos_session_close_view.xml',
        'views/pos_session_view.xml',
        'views/pos_config_view.xml',

        'wizard/poss_session_close_wizard_view.xml',
        'report/settlement_report.xml',
        'report/settlement_report_template.xml',
    ],
    'demo': [],
    'qweb': [

    ],
    'installable': True,
    'application': True,
    'auto_install': False,
}
