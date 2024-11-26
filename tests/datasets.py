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

from psebpconnector.models import *

ADDRESSES = {
    123456: Address(id=123456,
        id_customer=123456,
        id_manufacturer=123,
        id_supplier=0,
        id_warehouse=0,
        id_country=8,
        id_state=0,
        alias='RockPOS',
        company='',
        lastname='Dupont',
        firstname='Jean',
        vat_number=0,
        address1='N/A',
        address2='',
        postcode='',
        city='N/A',
        other='',
        phone='',
        phone_mobile='',
        dni='0000000000',
        deleted=0,
        date_add='2024-09-25 14:18:37',
        date_upd='2024-09-25 14:18:37')
}

COUNTRIES = {
    8: 'FR'
}

CURRENCIES = {
    1: 'EUR'
}

PRODUCTS = {
    123456: Product(id=123456,
                    price=37.500000,
                    ean13='4573102667311',
                    name=[{'value':'Product 1'}],
                    wholesale_price='24.255000',
                    description='desc Product 1'),
    654321: Product(id=654321,
                    price=65.833333,
                    ean13='987654321098',
                    name=[{'value':'Product 2'}],
                    wholesale_price='44.100000',
                    description='desc Product 2')
}

SINGLE_ORDER_WITH_TWO_PRODUCTS_BAD_AMOUNT = [
    Order(
        id=123456,
        id_address_delivery=123456,
        id_address_invoice=123456,
        id_cart=123456,
        id_currency=1,
        id_lang=1,
        id_customer=123456,
        id_carrier=0,
        id_shop_group=1,
        id_shop=1,
        associations={'order_rows': [{'id': 123456,
                                      'product_id': 123456,
                                      'product_attribute_id': 0,
                                      'product_quantity': 1,
                                      'product_name': 'Product 1',
                                      'product_reference': '0123456789012',
                                      'product_ean13': '0123456789012',
                                      'product_isbn': '',
                                      'product_upc': '',
                                      'product_price': '37.500000',
                                      'id_customization': 0,
                                      'unit_price_tax_incl': '45.000000',
                                      'unit_price_tax_excl': '37.500000'
                                      },
                                     {'id': 999999,
                                      'product_id': 654321,
                                      'product_attribute_id': 0,
                                      'product_quantity': 1,
                                      'product_name': 'Product 2',
                                      'product_reference': '987654321098',
                                      'product_ean13': '987654321098',
                                      'product_isbn': '',
                                      'product_upc': '',
                                      'product_price': '65.833333',
                                      'id_customization': 0,
                                      'unit_price_tax_incl': '79.000000',
                                      'unit_price_tax_excl': '65.833300'}
                                     ]},
        date_add='2024-11-13 10:00:00',
        conversion_rate='1.000000',
        current_state=2,
        delivery_date='2024-11-13 11:11:11',
        delivery_number=123456,
        invoice_date='2024-11-13 11:11:11',
        invoice_number=123456,
        module='feedbiz',
        payment='Ebay - FR - Creditcard',
        shipping_number='',
        total_discount=0,
        total_paid='52.500000',
        total_paid_real='105.000000',
        total_products='37.500000',
        total_products_wt='45.000000',
        total_shipping='7.500000',
        total_shipping_tax_incl='7.500000',
        total_shipping_tax_excl='6.250000',
    )
]

SINGLE_ORDER_WITH_UNKNOWN_PAYMENT_METHOD = [
    Order(
        id=123456,
        id_address_delivery=123456,
        id_address_invoice=123456,
        id_cart=123456,
        id_currency=1,
        id_lang=1,
        id_customer=123456,
        id_carrier=0,
        id_shop_group=1,
        id_shop=1,
        associations={'order_rows': [{'id': 123456,
                                      'product_id': 123456,
                                      'product_attribute_id': 0,
                                      'product_quantity': 1,
                                      'product_name': 'Product 1',
                                      'product_reference': '0123456789012',
                                      'product_ean13': '0123456789012',
                                      'product_isbn': '',
                                      'product_upc': '',
                                      'product_price': '37.500000',
                                      'id_customization': 0,
                                      'unit_price_tax_incl': '45.000000',
                                      'unit_price_tax_excl': '37.500000'
                                      },
                                     {'id': 999999,
                                      'product_id': 654321,
                                      'product_attribute_id': 0,
                                      'product_quantity': 1,
                                      'product_name': 'Product 2',
                                      'product_reference': '987654321098',
                                      'product_ean13': '987654321098',
                                      'product_isbn': '',
                                      'product_upc': '',
                                      'product_price': '65.833333',
                                      'id_customization': 0,
                                      'unit_price_tax_incl': '79.000000',
                                      'unit_price_tax_excl': '65.833300'}
                                     ]},
        date_add='2024-11-13 10:00:00',
        conversion_rate='1.000000',
        current_state=2,
        delivery_date='2024-11-13 11:11:11',
        delivery_number=123456,
        invoice_date='2024-11-13 11:11:11',
        invoice_number=123456,
        module='feedbiz',
        payment='FOO',
        shipping_number='',
        total_discount=0,
        total_paid='52.500000',
        total_paid_real='105.000000',
        total_products='37.500000',
        total_products_wt='45.000000',
        total_shipping='7.500000',
        total_shipping_tax_incl='7.500000',
        total_shipping_tax_excl='6.250000',
    )
]