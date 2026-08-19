# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError


class Print3dQuote(models.Model):
    _name = 'print3d.quote'
    _description = 'Cotización de Impresión 3D'
    _order = 'date desc, id desc'

    name = fields.Char(string='Referencia', required=True, copy=False, readonly=True, default=lambda self: _('Nueva'))
    state = fields.Selection([
        ('draft', 'Borrador'),
        ('confirmed', 'Confirmada'),
        ('cancelled', 'Cancelada'),
    ], string='Estado', default='draft', required=True, tracking=True)
    
    category_id = fields.Many2one('print3d.quote.category', string='Categoría')
    date = fields.Date(string='Fecha', default=fields.Date.context_today)
    description = fields.Text(string='Descripción del Trabajo / Pieza', required=True)
    image = fields.Image(string='Foto / Render (Principal)', max_width=1920, max_height=1920)
    image_ids = fields.One2many('print3d.quote.image', 'quote_id', string='Imágenes Adicionales')
    notes = fields.Text(string='Notas Internas')
    
    currency_id = fields.Many2one('res.currency', string='Moneda', default=lambda self: self.env.company.currency_id.id, required=True)

    # Costos configurables por cotización
    electricity_cost_kwh = fields.Float(string='Costo Eléctrico ($/kWh)', required=True)
    labor_cost_per_hour = fields.Float(string='Costo Mano de Obra ($/h)', required=True)
    
    # Líneas
    material_line_ids = fields.One2many('print3d.quote.material.line', 'quote_id', string='Filamentos')
    printer_line_ids = fields.One2many('print3d.quote.printer.line', 'quote_id', string='Equipos')
    supply_line_ids = fields.One2many('print3d.quote.supply.line', 'quote_id', string='Insumos')
    
    # Horas y Rentabilidad
    labor_hours = fields.Float(string='Horas de Mano de Obra')
    discount = fields.Float(string='Descuento (%)')
    margin = fields.Float(string='Margen de Ganancia (%)', required=True)

    # Costos Calculados
    cost_materials = fields.Monetary(string='Costo de Materiales', compute='_compute_costs', store=True, currency_field='currency_id')
    cost_energy = fields.Monetary(string='Costo Eléctrico', compute='_compute_costs', store=True, currency_field='currency_id')
    cost_wear = fields.Monetary(string='Costo de Desgaste', compute='_compute_costs', store=True, currency_field='currency_id')
    cost_labor = fields.Monetary(string='Costo Mano de Obra', compute='_compute_costs', store=True, currency_field='currency_id')
    cost_supplies = fields.Monetary(string='Costo Insumos', compute='_compute_costs', store=True, currency_field='currency_id')
    
    subtotal_cost = fields.Monetary(string='Costo Total', compute='_compute_costs', store=True, currency_field='currency_id')
    subtotal_with_margin = fields.Monetary(string='Subtotal c/Margen', compute='_compute_totals', store=True, currency_field='currency_id')
    discount_amount = fields.Monetary(string='Monto Descuento', compute='_compute_totals', store=True, currency_field='currency_id')
    total = fields.Monetary(string='Total Final', compute='_compute_totals', store=True, currency_field='currency_id')

    # Stock
    stock_alert = fields.Boolean(string='Alerta de Stock', compute='_compute_stock_alert')
    purchase_order_ids = fields.Many2many('purchase.order', string='Órdenes de Compra')
    purchase_count = fields.Integer(compute='_compute_purchase_count')
    
    sale_order_ids = fields.Many2many('sale.order', string='Órdenes de Venta')
    sale_order_count = fields.Integer(compute='_compute_sale_order_count')
    
    picking_ids = fields.Many2many('stock.picking', string='Movimientos de Inventario')
    picking_count = fields.Integer(compute='_compute_picking_count')



    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', _('Nueva')) == _('Nueva'):
                vals['name'] = self.env['ir.sequence'].next_by_code('print3d.quote') or _('Nueva')
        return super(Print3dQuote, self).create(vals_list)

    @api.model
    def default_get(self, fields_list):
        res = super(Print3dQuote, self).default_get(fields_list)
        ICPSudo = self.env['ir.config_parameter'].sudo()
        if 'electricity_cost_kwh' in fields_list and 'electricity_cost_kwh' not in res:
            res['electricity_cost_kwh'] = float(ICPSudo.get_param('print3d.electricity_cost_kwh', default=1.5))
        if 'labor_cost_per_hour' in fields_list and 'labor_cost_per_hour' not in res:
            res['labor_cost_per_hour'] = float(ICPSudo.get_param('print3d.labor_cost_per_hour', default=50.0))
        if 'margin' in fields_list and 'margin' not in res:
            res['margin'] = float(ICPSudo.get_param('print3d.default_margin', default=30.0))
        return res

    @api.depends('material_line_ids.cost', 'printer_line_ids.energy_cost', 'printer_line_ids.wear_cost', 
                 'supply_line_ids.subtotal', 'labor_hours', 'labor_cost_per_hour')
    def _compute_costs(self):
        for quote in self:
            quote.cost_materials = sum(quote.material_line_ids.mapped('cost'))
            quote.cost_energy = sum(quote.printer_line_ids.mapped('energy_cost'))
            quote.cost_wear = sum(quote.printer_line_ids.mapped('wear_cost'))
            quote.cost_supplies = sum(quote.supply_line_ids.mapped('subtotal'))
            quote.cost_labor = quote.labor_hours * quote.labor_cost_per_hour
            
            quote.subtotal_cost = quote.cost_materials + quote.cost_energy + quote.cost_wear + quote.cost_supplies + quote.cost_labor

    @api.depends('subtotal_cost', 'margin', 'discount')
    def _compute_totals(self):
        for quote in self:
            quote.subtotal_with_margin = quote.subtotal_cost * (1 + (quote.margin / 100.0))
            quote.discount_amount = quote.subtotal_with_margin * (quote.discount / 100.0)
            quote.total = quote.subtotal_with_margin - quote.discount_amount

    @api.depends('material_line_ids.stock_status')
    def _compute_stock_alert(self):
        for quote in self:
            quote.stock_alert = any(line.stock_status in ['low', 'empty'] for line in quote.material_line_ids)

    @api.depends('purchase_order_ids')
    def _compute_purchase_count(self):
        for quote in self:
            quote.purchase_count = len(quote.purchase_order_ids)

    @api.depends('sale_order_ids')
    def _compute_sale_order_count(self):
        for quote in self:
            quote.sale_order_count = len(quote.sale_order_ids)

    @api.depends('picking_ids')
    def _compute_picking_count(self):
        for quote in self:
            quote.picking_count = len(quote.picking_ids)




    def action_confirm(self):
        for quote in self:
            quote.state = 'confirmed'

    def action_cancel(self):
        for quote in self:
            quote.state = 'cancelled'

    def action_draft(self):
        for quote in self:
            quote.state = 'draft'

    def action_generate_po(self):
        """Genera órdenes de compra para los materiales con stock insuficiente."""
        self.ensure_one()
        materials_needed = {}
        
        for line in self.material_line_ids:
            if line.stock_status in ['low', 'empty'] and line.filament_id:
                needed_qty = (line.weight_grams / 1000.0)
                available = line.stock_qty
                qty_to_buy = needed_qty - available
                if qty_to_buy > 0:
                    product = line.filament_id
                    seller = product.seller_ids[0] if product.seller_ids else False
                    partner_id = seller.partner_id.id if seller else False
                    
                    if partner_id not in materials_needed:
                        materials_needed[partner_id] = []
                    materials_needed[partner_id].append({
                        'product_id': product.id,
                        'name': product.name,
                        'product_qty': qty_to_buy,
                        'product_uom': product.uom_po_id.id or product.uom_id.id,
                        'price_unit': seller.price if seller else product.standard_price,
                    })

        if not materials_needed:
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': 'Stock OK',
                    'message': 'No hay materiales con stock faltante para generar compra.',
                    'type': 'success',
                    'sticky': False,
                }
            }

        po_ids = []
        for partner_id, lines in materials_needed.items():
            if not partner_id:
                # Si no tiene proveedor, usar un proveedor dummy o lanzar error
                # Por ahora agrupamos los que no tienen proveedor sin crear PO
                continue
                
            po_vals = {
                'partner_id': partner_id,
                'origin': self.name,
                'order_line': [(0, 0, line) for line in lines]
            }
            po = self.env['purchase.order'].create(po_vals)
            po_ids.append(po.id)

        if po_ids:
            self.write({'purchase_order_ids': [(4, po_id) for po_id in po_ids]})
            
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': 'Órdenes de Compra',
                'message': f'Se generaron {len(po_ids)} órdenes de compra.',
                'type': 'success',
                'sticky': False,
            }
        }

    def action_view_purchases(self):
        self.ensure_one()
        return {
            'name': 'Órdenes de Compra',
            'type': 'ir.actions.act_window',
            'res_model': 'purchase.order',
            'domain': [('id', 'in', self.purchase_order_ids.ids)],
            'view_mode': 'tree,form',
        }

    def action_view_sales(self):
        self.ensure_one()
        return {
            'name': 'Órdenes de Venta',
            'type': 'ir.actions.act_window',
            'res_model': 'sale.order',
            'domain': [('id', 'in', self.sale_order_ids.ids)],
            'view_mode': 'tree,form',
        }

    def action_view_pickings(self):
        self.ensure_one()
        return {
            'name': 'Consumos de Inventario',
            'type': 'ir.actions.act_window',
            'res_model': 'stock.picking',
            'domain': [('id', 'in', self.picking_ids.ids)],
            'view_mode': 'tree,form',
        }

    def action_create_picking(self):
        self.ensure_one()
        if not self.material_line_ids:
            return

        # Buscar tipo de operación de salida (Delivery Order / Consumo)
        picking_type = self.env['stock.picking.type'].search([
            ('code', '=', 'outgoing'),
            ('company_id', '=', self.env.company.id)
        ], limit=1)
        
        if not picking_type:
            raise UserError(_('No se encontró un tipo de operación de salida (Delivery) configurado para la compañía.'))

        # Crear Picking (Albarán)
        # Buscar la ubicación de producción o clientes
        location_dest_id = self.env.ref('stock.stock_location_customers', raise_if_not_found=False)
        if not location_dest_id:
            location_dest_id = picking_type.default_location_dest_id
            
        picking = self.env['stock.picking'].create({
            'picking_type_id': picking_type.id,
            'location_id': picking_type.default_location_src_id.id,
            'location_dest_id': location_dest_id.id,
            'origin': self.name,
            'note': _('Consumo de materiales para la cotización %s', self.name),
        })

        uom_gram = self.env.ref('uom.product_uom_gram')

        # Añadir líneas de materiales
        for line in self.material_line_ids:
            if not line.filament_id:
                continue
            
            # Crear stock move en la UoM de Gramos, Odoo se encarga de convertir si el producto está en Kg
            self.env['stock.move'].create({
                'name': line.filament_id.name,
                'product_id': line.filament_id.id,
                'product_uom_qty': line.weight_grams,
                'product_uom': uom_gram.id,
                'picking_id': picking.id,
                'location_id': picking.location_id.id,
                'location_dest_id': picking.location_dest_id.id,
            })

        # Confirmar el picking
        picking.action_confirm()
        # Automáticamente asignar y validar el picking si es necesario, pero es mejor dejarlo en listo
        # picking.action_assign()
        # picking.button_validate() # Para validarlo automáticamente, requiere asignar lotes si aplica. 
        # Dejaremos que el usuario lo valide o se quede como pendiente según su flujo.

        self.write({'picking_ids': [(4, picking.id)]})
        return picking



class Print3dQuoteMaterialLine(models.Model):
    _name = 'print3d.quote.material.line'
    _description = 'Línea de Material (Filamento) para Cotización'

    quote_id = fields.Many2one('print3d.quote', string='Cotización', ondelete='cascade', required=True)
    
    # Búsqueda por atributos
    attr_material_type = fields.Many2one('product.attribute.value', string='Tipo', domain="[('attribute_id.name', '=', 'Tipo de Material')]")
    attr_finish = fields.Many2one('product.attribute.value', string='Acabado', domain="[('attribute_id.name', '=', 'Acabado')]")
    attr_color = fields.Many2one('product.attribute.value', string='Color', domain="[('attribute_id.name', '=', 'Color')]")
    html_color = fields.Char(string='Muestra', related='attr_color.html_color', readonly=True)

    
    filament_id = fields.Many2one('product.product', string='Filamento', compute='_compute_filament', store=True, readonly=False)
    
    weight_grams = fields.Float(string='Peso (g)', required=True, default=0.0)
    price_per_kg = fields.Float(string='Precio / kg', compute='_compute_price', store=True, readonly=False)
    cost = fields.Float(string='Costo', compute='_compute_cost', store=True)
    
    stock_qty = fields.Float(string='Stock (g)', compute='_compute_stock')
    stock_status = fields.Selection([
        ('ok', 'Suficiente'),
        ('low', 'Bajo'),
        ('empty', 'Agotado')
    ], string='Estado de Stock', compute='_compute_stock')
    
    notes = fields.Char(string='Notas')

    @api.depends('attr_material_type', 'attr_finish', 'attr_color')
    def _compute_filament(self):
        for line in self:
            domain = [('categ_id.name', '=', 'Filamentos 3D')]
            if line.attr_material_type:
                domain.append(('product_template_attribute_value_ids.product_attribute_value_id', '=', line.attr_material_type.id))
            if line.attr_finish:
                domain.append(('product_template_attribute_value_ids.product_attribute_value_id', '=', line.attr_finish.id))
            if line.attr_color:
                domain.append(('product_template_attribute_value_ids.product_attribute_value_id', '=', line.attr_color.id))
            
            # Buscar el producto que coincida
            if domain != [('categ_id.name', '=', 'Filamentos 3D')]: # Solo si hay al menos un filtro
                product = self.env['product.product'].search(domain, limit=1)
                if product:
                    line.filament_id = product
                # Si no encuentra, no blanquea automáticamente para permitir selección manual si falla el filtro

    @api.depends('filament_id')
    def _compute_price(self):
        for line in self:
            if line.filament_id:
                line.price_per_kg = line.filament_id.standard_price

    @api.depends('weight_grams', 'price_per_kg')
    def _compute_cost(self):
        for line in self:
            line.cost = (line.weight_grams / 1000.0) * line.price_per_kg

    @api.depends('filament_id', 'weight_grams')
    def _compute_stock(self):
        uom_gram = self.env.ref('uom.product_uom_gram', raise_if_not_found=False)
        for line in self:
            if line.filament_id and uom_gram:
                # Convertir stock disponible a gramos
                available_grams = line.filament_id.uom_id._compute_quantity(line.filament_id.qty_available, uom_gram)
                needed_grams = line.weight_grams
                
                line.stock_qty = available_grams
                if available_grams >= needed_grams:
                    line.stock_status = 'ok'
                elif available_grams > 0:
                    line.stock_status = 'low'
                else:
                    line.stock_status = 'empty'
            else:
                line.stock_qty = 0.0
                line.stock_status = 'empty'



class Print3dQuotePrinterLine(models.Model):
    _name = 'print3d.quote.printer.line'
    _description = 'Línea de Impresora para Cotización'

    quote_id = fields.Many2one('print3d.quote', string='Cotización', ondelete='cascade', required=True)
    printer_id = fields.Many2one('print3d.printer', string='Impresora', required=True)
    
    print_hours = fields.Float(string='Horas de Impresión', required=True, default=0.0)
    power_kw = fields.Float(string='Consumo (kW)', compute='_compute_printer_data', store=True, readonly=False)
    depreciation_per_hour = fields.Float(string='Desgaste/h', compute='_compute_printer_data', store=True, readonly=False)
    
    electricity_cost_kwh = fields.Float(related='quote_id.electricity_cost_kwh')
    
    energy_cost = fields.Float(string='Costo Eléctrico', compute='_compute_costs', store=True)
    wear_cost = fields.Float(string='Costo Desgaste', compute='_compute_costs', store=True)
    total_cost = fields.Float(string='Total Costo', compute='_compute_costs', store=True)

    @api.depends('printer_id')
    def _compute_printer_data(self):
        for line in self:
            if line.printer_id:
                line.power_kw = line.printer_id.power_consumption_kw
                line.depreciation_per_hour = line.printer_id.depreciation_per_hour

    @api.depends('print_hours', 'power_kw', 'electricity_cost_kwh', 'depreciation_per_hour')
    def _compute_costs(self):
        for line in self:
            line.energy_cost = line.print_hours * line.power_kw * line.electricity_cost_kwh
            line.wear_cost = line.print_hours * line.depreciation_per_hour
            line.total_cost = line.energy_cost + line.wear_cost


class Print3dQuoteSupplyLine(models.Model):
    _name = 'print3d.quote.supply.line'
    _description = 'Línea de Insumo para Cotización'

    quote_id = fields.Many2one('print3d.quote', string='Cotización', ondelete='cascade', required=True)
    product_id = fields.Many2one('product.product', string='Insumo', required=True)
    
    quantity = fields.Float(string='Cantidad', required=True, default=1.0)
    price_unit = fields.Float(string='Precio Unitario', compute='_compute_price_unit', store=True, readonly=False)
    subtotal = fields.Float(string='Subtotal', compute='_compute_subtotal', store=True)

    @api.depends('product_id')
    def _compute_price_unit(self):
        for line in self:
            if line.product_id:
                line.price_unit = line.product_id.standard_price

    @api.depends('quantity', 'price_unit')
    def _compute_subtotal(self):
        for line in self:
            line.subtotal = line.quantity * line.price_unit

class Print3dQuoteImage(models.Model):
    _name = 'print3d.quote.image'
    _description = 'Imagen de Cotización 3D'

    quote_id = fields.Many2one('print3d.quote', string='Cotización', required=True, ondelete='cascade')
    name = fields.Char(string='Nombre')
    image = fields.Image(string='Imagen', required=True, max_width=1920, max_height=1920)

