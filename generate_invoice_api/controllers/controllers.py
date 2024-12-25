import json
import logging
from odoo import http
from odoo.http import request

# Set up logging
_logger = logging.getLogger(__name__)

class InvoiceAPI(http.Controller):
    @http.route('/api/create_invoice', type='json', auth='public', methods=['POST'])
    def create_invoice(self, **kwargs):
        try:
            # Extract the JSON body of the request
            data = request.jsonrequest

            # Extract and validate data from the request
            partner_id = data.get('partner_id')
            invoice_lines = data.get('invoice_lines')
            currency_id = data.get('currency_id')
            currency_code = data.get('currency_code')  # Currency code from request
            total_amount_before_tax = data.get('total_amount_before_tax')  # Direct value from request
            total_tax = data.get('total_tax')  # Direct value from request
            total_discount = data.get('total_discount')  # Direct value from request
            total_amount_after_tax = data.get('total_amount_after_tax')  # Direct value from request
            total_payment = data.get('total_payment')  # Direct value from request
            payment_reference = data.get('payment_reference')  # Payment Reference from request
            invoice_date = data.get('invoice_date')  # Invoice Date from request
            payment_method = data.get('payment_method')  # Payment Method from request

            # Log the received data for debugging
            _logger.info("Received Data:")
            _logger.info(f"partner_id: {partner_id}")
            _logger.info(f"invoice_lines: {invoice_lines}")
            _logger.info(f"currency_id: {currency_id}")
            _logger.info(f"currency_code: {currency_code}")
            _logger.info(f"total_amount_before_tax: {total_amount_before_tax}")
            _logger.info(f"total_tax: {total_tax}")
            _logger.info(f"total_discount: {total_discount}")
            _logger.info(f"total_amount_after_tax: {total_amount_after_tax}")
            _logger.info(f"total_payment: {total_payment}")
            _logger.info(f"payment_reference: {payment_reference}")
            _logger.info(f"invoice_date: {invoice_date}")
            _logger.info(f"payment_method: {payment_method}")

            # Validate mandatory fields
            if not partner_id:
                return {'status': 'error', 'message': 'Missing "partner_id"'}
            if not invoice_lines or not isinstance(invoice_lines, list):
                return {'status': 'error', 'message': '"invoice_lines" must be a non-empty list'}
            if not currency_id:
                return {'status': 'error', 'message': 'Missing "currency_id"'}

            # Validate each invoice line
            for line in invoice_lines:
                if not isinstance(line, dict):
                    return {'status': 'error', 'message': 'Each invoice line must be a dictionary'}
                if not line.get('product_id'):
                    return {'status': 'error', 'message': 'Each invoice line must have a "product_id"'}
                if not isinstance(line.get('quantity', 1), (int, float)):
                    return {'status': 'error', 'message': 'Quantity must be a number'}
                if not isinstance(line.get('price_unit', 0), (int, float)):
                    return {'status': 'error', 'message': 'Price unit must be a number'}

            # Set default invoice date if not provided
            if not invoice_date:
                invoice_date = fields.Date.today()

            # Create the invoice
            invoice_vals = {
                'partner_id': int(partner_id),
                'currency_id': int(currency_id),
                'move_type': 'out_invoice',  # Customer Invoice
                'invoice_line_ids': [
                    (0, 0, {
                        'product_id': line['product_id'],
                        'quantity': line.get('quantity', 1),
                        'price_unit': line.get('price_unit', 0),
                    }) for line in invoice_lines
                ],
                'currency_code': currency_code,
                'total_amount_before_tax': total_amount_before_tax,
                'total_tax': total_tax,
                'total_discount': total_discount,
                'total_amount_after_tax': total_amount_after_tax,
                'total_payment': total_payment,
                'payment_reference': payment_reference,  # Add Payment Reference
                'invoice_date': invoice_date,  # Set the Invoice Date
                'payment_method': payment_method,  # Payment Method
            }

            # Create invoice record
            invoice = request.env['account.move'].sudo().create(invoice_vals)

            return {'status': 'success', 'invoice_id': invoice.id, 'currency_code': currency_code,
                    'total_amount_after_tax': total_amount_after_tax, 'total_amount_before_tax': total_amount_before_tax,
                    'total_tax': total_tax, 'total_discount': total_discount, 'total_payment': total_payment}

        except KeyError as e:
            _logger.error(f'Missing required field: {str(e)}')
            return {'status': 'error', 'message': f'Missing required field: {str(e)}'}
        except ValueError as e:
            _logger.error(f'Invalid value provided: {str(e)}')
            return {'status': 'error', 'message': f'Invalid value provided: {str(e)}'}
        except Exception as e:
            # Log the error and rollback in case of database errors
            _logger.error(f'An unexpected error occurred: {str(e)}')
            request.env.cr.rollback()  # Rollback in case of database errors
            return {'status': 'error', 'message': f'An unexpected error occurred: {str(e)}'}
