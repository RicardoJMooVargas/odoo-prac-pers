# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError

class Print3dQuoteMakeSale(models.TransientModel):
    _name = 'print3d.quote.make.sale'
    _description = 'Crear Venta desde Cotización 3D'

    partner_id = fields.Many2one('res.partner', string='Cliente', required=True)

    def action_create_sale_order(self):
        self.ensure_one()
        quote_id = self.env.context.get('active_id')
        if not quote_id:
            return

        quote = self.env['print3d.quote'].browse(quote_id)
        if quote.state != 'confirmed':
            raise UserError(_("La cotización debe estar confirmada para generar una venta."))

        # Buscar o crear el producto "Servicio de Impresión 3D"
        product = self.env['product.product'].search([('name', '=', 'Servicio de Impresión 3D')], limit=1)
        if not product:
            product = self.env['product.product'].create({
                'name': 'Servicio de Impresión 3D',
                'type': 'service',
                'invoice_policy': 'order',
                'list_price': 0.0,
            })

        # Crear la Orden de Venta
        sale_order = self.env['sale.order'].create({
            'partner_id': self.partner_id.id,
            'client_order_ref': quote.name,
            'origin': quote.name,
            'order_line': [(0, 0, {
                'product_id': product.id,
                'name': f"{quote.name} - {quote.description}",
                'product_uom_qty': 1,
                'price_unit': quote.total,
            })]
        })

        # Vincular la venta a la cotización
        quote.write({'sale_order_ids': [(4, sale_order.id)]})

        # Descontar el material del inventario
        quote.action_create_picking()

        # Retornar acción para abrir la nueva orden de venta
        return {
            'name': _('Orden de Venta'),
            'type': 'ir.actions.act_window',
            'res_model': 'sale.order',
            'res_id': sale_order.id,
            'view_mode': 'form',
            'target': 'current',
        }
