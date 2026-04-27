{
    'name': 'POS Config Session Management',
    'version': '14.1',
    'summary': 'Manage config session assess of pos users and manager',
    'sequence': 10,
    "author": "'Divergent Catalist Pvt ltd'",
    "website": "https://www.catalisterp.com",
    'description': """The module used to manage access of pos users. pos manager can assess all config session in pos system and 
                       pos user can view only assigned config session """,
    'category': 'Point of Sale',
    'depends': ['base', 'point_of_sale', 'pos_manager_validation_mac5'],
    'data': [
        # 'security/ir.model.access.csv',
        'security/pos_session_management_security.xml',
        'views/pos_session_view.xml'
    ],
    'demo': [],
    'installable': True,
    'application': True,
    'auto_install': False,
}
