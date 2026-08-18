# -*- coding: utf-8 -*-
from odoo import models, fields, api

class Print3dConfig(models.TransientModel):
    _name = 'print3d.config'
    _description = 'Configuración global de Impresión 3D'

    electricity_cost_kwh = fields.Float(
        string='Costo de Electricidad ($/kWh)',
        default=1.5,
        help="Costo promedio de electricidad por kWh."
    )
    labor_cost_per_hour = fields.Float(
        string='Costo de Mano de Obra ($/h)',
        default=50.0,
        help="Costo por hora de mano de obra."
    )
    default_margin = fields.Float(
        string='Margen de Ganancia por Defecto (%)',
        default=30.0,
        help="Margen de ganancia general para nuevas cotizaciones."
    )

    @api.model
    def get_values(self):
        # We need to fetch parameters from ir.config_parameter
        ICPSudo = self.env['ir.config_parameter'].sudo()
        electricity_cost_kwh = float(ICPSudo.get_param('print3d.electricity_cost_kwh', default=1.5))
        labor_cost_per_hour = float(ICPSudo.get_param('print3d.labor_cost_per_hour', default=50.0))
        default_margin = float(ICPSudo.get_param('print3d.default_margin', default=30.0))
        
        # Use transient model structure, this must return a dict
        res = super(Print3dConfig, self).get_values()
        res.update(
            electricity_cost_kwh=electricity_cost_kwh,
            labor_cost_per_hour=labor_cost_per_hour,
            default_margin=default_margin,
        )
        return res

    def set_values(self):
        super(Print3dConfig, self).set_values()
        ICPSudo = self.env['ir.config_parameter'].sudo()
        ICPSudo.set_param('print3d.electricity_cost_kwh', self.electricity_cost_kwh)
        ICPSudo.set_param('print3d.labor_cost_per_hour', self.labor_cost_per_hour)
        ICPSudo.set_param('print3d.default_margin', self.default_margin)
