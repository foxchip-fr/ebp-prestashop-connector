"""
MIT License

Copyright (c) 2024 Foxchip

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""

from dataclasses import dataclass


@dataclass
class ExportOrderRow:
    document_use_original_number: str
    document_number_prefix: str
    document_number_suffix: str
    document_number: str
    document_date: str
    document_client_code: str
    document_civil: str
    document_client_name: str
    document_invoice_address_1: str
    document_invoice_address_2: str
    document_invoice_address_3: str
    document_invoice_address_4: str
    document_invoice_zip_code: str
    document_invoice_city: str
    document_invoice_department: str
    document_invoice_country_iso_code: str
    document_invoice_lastname: str
    document_invoice_firstname: str
    document_invoice_phone: str
    document_invoice_mobile_phone: str
    document_invoice_fax: str
    document_invoice_email: str
    document_delivery_address_1: str
    document_delivery_address_2: str
    document_delivery_address_3: str
    document_delivery_address_4: str
    document_delivery_zip_code: str
    document_delivery_city: str
    document_delivery_department: str
    document_delivery_country_iso_code: str
    document_delivery_lastname: str
    document_delivery_firstname: str
    document_delivery_phone: str
    document_delivery_mobile_phone: str
    document_delivery_fax: str
    document_delivery_email: str
    document_territoriality: str
    document_vat_number: str
    document_discount_pct: str
    document_discount_amount: str
    document_escompte_pct: str
    document_escompte_amount: str
    document_shipping_cost_code: str
    document_shipping_cost_notax: str
    document_shipping_cost_vat_rate: str
    document_shipping_tva_code: str
    document_total_notax: str
    document_total: str
    document_notes: str
    line_product_code: str
    line_description: str
    line_quantity: str
    line_vat_rate: str
    line_vat_code: str
    document_commercial_code: str
    line_unit_price_notax: str
    line_unit_price: str
    line_discount_pct: str
    line_discount_notax: str
    line_price_notax: str
    line_price: str
    line_commercial_code: str
    document_payment_method: str
    deposit_amount: str
    deposit_payment_method: str
    deposit_date: str
    document_ignore_prices: str
    document_name_delivery_address: str
    document_depot: str
    document_currency_rate: str
    document_currency_iso_code: str
    deposit_amount_currency: str
    deposit_currency_rate: str
    deposit_currency_iso_code: str
    document_currency_amount: str
    document_currency_amount_notax: str
    document_currency_amount_shipping_notax: str
    line_currency_unit_price_notax: str
    line_currency_cumulative_discount_amount_notax: str
    line_currency_total_notax: str
    document_currency_used: str
    document_series: str
    document_business_code: str
    mroad_id: str
    mroad_technicality: str
    document_client_order_number: str
    line_ignore_linked_products: str
    document_language: str
