# -*- coding: utf-8 -*-
{
    'name': 'Cotizaciones Impresión 3D',
    'version': '17.0.1.0.0',
    'summary': 'Gestión de cotizaciones para trabajos de impresión 3D',
    'description': """
        Módulo para calcular y gestionar cotizaciones de impresión 3D.
        Incluye control de materiales (filamentos), equipos, insumos,
        costos de electricidad, mano de obra y desgaste de equipos.
        Integración con inventario para verificación de stock de filamentos.
    """,
    'category': 'Manufacturing',
    'author': 'Mi Empresa',
    'license': 'LGPL-3',
    'depends': [
        'base',
        'product',
        'stock',
        'purchase',
        'mail',
        'sale_management',
    ],
    'data': [
        'security/ir.model.access.csv',
        'data/print3d_sequence.xml',
        'data/print3d_product_data.xml',
        'data/print3d_category_data.xml',
        'views/print3d_config_views.xml',
        'views/print3d_printer_views.xml',
        'views/print3d_quote_category_views.xml',
        'views/print3d_quote_views.xml',
        'wizard/print3d_quote_make_sale_views.xml',
        'views/menus.xml',
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
}
