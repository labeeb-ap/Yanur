{
    'name': 'Employee Categorisation',
    'description': 'An inherited module for categorize the employees as permanent or probation',
    'depends': ['base', 'hr', 'hr_holidays', 'hr_payroll_community'],
    'data': ['security/ir.model.access.csv',
             'data/sequence.xml',
             'views/hr_employee_views.xml',
             'views/hr_leave_views.xml',
             'views/hr_contract_view.xml',
             'views/hr_payslip_view.xml',
             'wizard/partial_payment_wizard_view.xml',
             ]

}