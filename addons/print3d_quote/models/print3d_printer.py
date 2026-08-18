# -*- coding: utf-8 -*-
from odoo import models, fields, api

class Print3dPrinter(models.Model):
    _name = 'print3d.printer'
    _description = 'Impresora 3D'

    name = fields.Char(string='Nombre del Equipo', required=True)
    purchase_price = fields.Float(string='Precio de Compra', required=True, default=0.0)
    power_consumption_kw = fields.Float(string='Consumo Eléctrico (kW)', required=True, default=0.0, help="Ej. 0.35 para 350W")
    lifespan_hours = fields.Float(string='Vida Útil Estimada (Horas)', required=True, default=10000.0)
    
    depreciation_per_hour = fields.Float(
        string='Desgaste por Hora', 
        compute='_compute_depreciation', 
        store=True,
        help="Cálculo automático: Precio de Compra / Vida Útil Estimada"
    )
    
    active = fields.Boolean(string='Activo', default=True)
    notes = fields.Text(string='Notas Técnicas')

    @api.depends('purchase_price', 'lifespan_hours')
    def _compute_depreciation(self):
        for printer in self:
            if printer.lifespan_hours > 0:
                printer.depreciation_per_hour = printer.purchase_price / printer.lifespan_hours
            else:
                printer.depreciation_per_hour = 0.0
