# -*- coding: utf-8 -*-
from odoo import models, fields, api

class Print3dQuoteCategory(models.Model):
    _name = 'print3d.quote.category'
    _description = 'Categoría de Cotización de Impresión 3D'
    _parent_name = "parent_id"
    _parent_store = True
    _rec_name = 'name'
    _order = 'name'

    name = fields.Char(string='Nombre', required=True)
    description = fields.Text(string='Descripción')
    parent_id = fields.Many2one('print3d.quote.category', string='Categoría Padre', index=True, ondelete='cascade')
    child_ids = fields.One2many('print3d.quote.category', 'parent_id', string='Subcategorías')
    parent_path = fields.Char(index=True, unaccent=False)
    
    color = fields.Integer(string='Color')
    
    quote_ids = fields.One2many('print3d.quote', 'category_id', string='Cotizaciones')
    quote_count = fields.Integer(string='N° de Cotizaciones', compute='_compute_quote_count')

    @api.depends('quote_ids')
    def _compute_quote_count(self):
        for category in self:
            category.quote_count = len(category.quote_ids)

    def name_get(self):
        res = []
        for category in self:
            name = category.name
            if category.parent_id:
                name = f"{category.parent_id.name} / {name}"
            res.append((category.id, name))
        return res
