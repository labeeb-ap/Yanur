{
    "name": "Partner Statment Report",
    "summary": """Partner Statment Report""",
    "category": "Accounting",
    "version": "1.1.1",
    "sequence": 1,
    "depends": ['account'],
    "data": [
        'security/ir.model.access.csv',
        # 'data/partner_statement_report_template.xml',
        'report/partner_statement_pdf_report.xml',
        'report/statement_report_pdf.xml',
        'wizard/partner_statement_report.xml',
        'views/action_manager.xml',

        # 'report/report.xml',
    ],
    "demo": [],
    "application": True,
    "installable": True,
    "auto_install": False,
    # "pre_init_hook": "pre_init_check",
}
