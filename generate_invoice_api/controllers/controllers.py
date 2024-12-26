import logging
from odoo import http, fields
from odoo.http import request

_logger = logging.getLogger(__name__)

class InvoiceAPI(http.Controller):
    @http.route('/api/create_invoice', type='json', auth='public', methods=['POST'])
    def create_invoice(self, **kwargs):
        try:
            # Extract the JSON body of the request
            data = request.jsonrequest

            # Extract and validate data for customer profile
            customer_data = {
                "name": f"{data.get('FirstName', '')} {data.get('LastName', '')}".strip(),
                "gender": data.get("Gender", ""),
                "birth_date": data.get("DateOfBirth", ""),
                "spouse_birth_date": data.get("SpouseDateOfBirth", ""),
                "wedding_anniversary": data.get("WeddingAnniversary", ""),
                "street": data.get("Address", ""),
                "city": data.get("City", ""),
                "state_id": data.get("State", ""),
                "country_id": data.get("Country", ""),
                "nationality": data.get("Nationality", ""),
                "zip": data.get("Zipcode", ""),
                "phone": data.get("Phone", ""),
                "mobile": data.get("Mobile", ""),
                "fax": data.get("Fax", ""),
                "email": data.get("Email", ""),
            }

            # Extract and validate invoice data
            invoice_lines = data.get('invoice_lines')
            currency_id = data.get('currency_id')
            total_amount_before_tax = data.get('total_amount_before_tax')
            total_tax = data.get('total_tax')
            total_discount = data.get('total_discount')
            total_amount_after_tax = data.get('total_amount_after_tax')
            total_payment = data.get('total_payment')
            payment_reference = data.get('payment_reference')
            invoice_date = data.get('invoice_date')
            payment_method = data.get('payment_method')

            # Validate mandatory fields
            if not customer_data["name"]:
                return {'status': 'error', 'message': 'Missing customer name (FirstName and/or LastName)'}
            if not invoice_lines or not isinstance(invoice_lines, list):
                return {'status': 'error', 'message': '"invoice_lines" must be a non-empty list'}
            if not currency_id:
                return {'status': 'error', 'message': 'Missing "currency_id"'}

            # Search for the customer (partner) by email or phone
            partner = request.env['res.partner'].sudo().search(
                ['|', ('email', '=', customer_data['email']), ('mobile', '=', customer_data['mobile'])], limit=1)

            # If the customer doesn't exist, create it
            if not partner:
                _logger.info(f"Customer not found, creating a new customer profile: {customer_data}")
                partner_vals = {
                    'name': customer_data['name'],
                    'email': customer_data['email'],
                    'mobile': customer_data['mobile'],
                    'phone': customer_data['phone'],
                    'street': customer_data['street'],
                    'city': customer_data['city'],
                    'zip': customer_data['zip'],
                    'country_id': self._get_country_id(customer_data['country_id']),
                    'state_id': self._get_state_id(customer_data['state_id']),
                }
                partner = request.env['res.partner'].sudo().create(partner_vals)
                _logger.info(f"Customer created with ID {partner.id}.")

            # Set default invoice date if not provided
            if not invoice_date:
                invoice_date = fields.Date.today()

            # Create the invoice lines
            invoice_line_ids = []
            for line in invoice_lines:
                product_name = line.get('product_name')
                product = request.env['product.product'].sudo().search([('name', '=', product_name)], limit=1)

                if not product:
                    # If product not found, create it
                    _logger.info(f"Product '{product_name}' not found, creating a new product.")
                    product_vals = {
                        'name': product_name,
                        'type': 'service',  # Default product type, can be modified as needed
                        'list_price': line.get('price_unit', 0),
                    }
                    product = request.env['product.product'].sudo().create(product_vals)
                    _logger.info(f"Product created with ID {product.id}.")

                # Add line to invoice
                invoice_line_ids.append((0, 0, {
                    'product_id': product.id,
                    'quantity': line.get('quantity', 1),
                    'price_unit': line.get('price_unit', 0),
                }))

            # Create the invoice
            invoice_vals = {
                'partner_id': partner.id,
                'currency_id': self._get_currency_id(currency_id),  # Use the helper method to get the correct currency_id
                'move_type': 'out_invoice',  # Customer Invoice
                'invoice_line_ids': invoice_line_ids,
                'invoice_date': invoice_date,  # Set the Invoice Date
                'payment_reference': payment_reference,  # Add Payment Reference
            }

            # Create invoice record
            invoice = request.env['account.move'].sudo().create(invoice_vals)

            return {
                'status': 'success',
                'customer_id': partner.id,
                'invoice_id': invoice.id,
                'total_amount_after_tax': total_amount_after_tax,
                'total_amount_before_tax': total_amount_before_tax,
                'total_tax': total_tax,
                'total_discount': total_discount,
                'total_payment': total_payment
            }

        except KeyError as e:
            _logger.error(f'Missing required field: {str(e)}')
            return {'status': 'error', 'message': f'Missing required field: {str(e)}'}
        except ValueError as e:
            _logger.error(f'Invalid value provided: {str(e)}')
            return {'status': 'error', 'message': f'Invalid value provided: {str(e)}'}
        except Exception as e:
            _logger.error(f'An unexpected error occurred: {str(e)}')
            request.env.cr.rollback()  # Rollback in case of database errors
            return {'status': 'error', 'message': f'An unexpected error occurred: {str(e)}'}

    def _get_country_id(self, country_name):
        """Helper method to find or create country by name."""
        country = request.env['res.country'].sudo().search([('name', '=', country_name)], limit=1)
        return country.id if country else False

    def _get_state_id(self, state_name):
        """Helper method to find or create state by name."""
        state = request.env['res.country.state'].sudo().search([('name', '=', state_name)], limit=1)
        return state.id if state else False

    def _get_currency_id(self, currency_code):
        """Helper method to find the currency by its code."""
        currency = request.env['res.currency'].sudo().search([('name', '=', currency_code)], limit=1)
        return currency.id if currency else False
