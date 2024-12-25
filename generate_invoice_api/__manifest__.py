# -*- coding: utf-8 -*-
{
    'name': "Generate Invoice API",

    'summary': """
        generate_invoice_api""",

    'description': """
        generate_invoice_api
    """,

    'author': "Majid Saqe",
    'website': "https://github.com/majidsaqr12",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/15.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Uncategorized',
    'version': '0.1',
    'sequence': '-600',

    # any module necessary for this one to work correctly
    'depends': ['base', 'account'],

    # always loaded
    'data': [
        # 'security/ir.model.access.csv',
        'views/views.xml',
        'views/templates.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
        'demo/demo.xml',
    ],
    
    'installable': True,
    'application': True,
    'auto_install': False,
    'license': 'LGPL-3',
}
