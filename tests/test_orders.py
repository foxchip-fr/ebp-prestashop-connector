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

import pytest

from .datasets import *
from .fixtures import offline_connector
from psebpconnector.export_models import ExportOrderRow, ExportProduct


EXPORTED_ORDERS = []
EXPORTED_PRODUCTS = []

EXPECTED_RESULTS = [
    (
        # Simple case
        SINGLE_ORDER_FR_ONE_PRODUCT,
        (
            [{
                'document_use_original_number': 'N',
                'line_quantity': '1',
                'line_vat_rate': '20.000000',
                'line_unit_price': '39.000000',
                'document_payment_method': 'PAYPAL',
                'document_currency_rate': '',
                'line_vat_code': '36cab0de-3e5b-4bee-a556-8eabb1673e76'
            }],
            [{
                'code': '1111111111111',
                'name': 'Product 1',
                'type': 'BIEN',
                'price': '32.500000',
                'ean': '1111111111111',
                'wholesale_price': '20.700000'
            }]
        )
    ),
    (
        # Should export only one product
        SINGLE_ORDER_FR_ONE_PRODUCT*2,
        (
            [{
                'document_use_original_number': 'N',
                'line_quantity': '1',
                'line_vat_rate': '20.000000',
                'line_unit_price': '39.000000',
                'document_payment_method': 'PAYPAL',
                'document_currency_rate': '',
                'line_vat_code': '36cab0de-3e5b-4bee-a556-8eabb1673e76'
            }]*2,
            [{
                'code': '1111111111111',
                'name': 'Product 1',
                'type': 'BIEN',
                'price': '32.500000',
                'ean': '1111111111111',
                'wholesale_price': '20.700000'
            }]
        )
    )
]

def _fake_write_csv_line(_, obj, __):
    global EXPORTED_PRODUCTS
    global EXPORTED_ORDERS

    if isinstance(obj, ExportOrderRow):
        EXPORTED_ORDERS.append(obj)
    elif isinstance(obj, ExportProduct):
        EXPORTED_PRODUCTS.append(obj)
    else:
        raise TypeError(type(obj))


@pytest.mark.parametrize("should", EXPECTED_RESULTS)
def test_order(offline_connector, mocker, should):
    global EXPORTED_ORDERS
    global EXPORTED_PRODUCTS

    EXPORTED_ORDERS = []
    EXPORTED_PRODUCTS = []

    orders = should[0]
    should_orders = should[1][0]
    should_products = should[1][1]

    mocker.patch("psebpconnector.webservice.Webservice.get_orders_to_export", return_value=orders)
    mocker.patch('psebpconnector.connector.Connector._write_csv_line', new=_fake_write_csv_line)

    assert offline_connector.run() == 0
    assert len(should_orders) == len(EXPORTED_ORDERS)
    assert len(should_products) == len(EXPORTED_PRODUCTS)

    # Orders
    for i in range(len(should_orders)):
        for key, value in should_orders[i].items():
            assert getattr(EXPORTED_ORDERS[i], key) == value, f"Wrong value for field {key}, order row n°{i+1}"

    # Products
    for i in range(len(should_products)):
        for key, value in should_products[i].items():
            assert getattr(EXPORTED_PRODUCTS[i], key) == value, f"Wrong value for field {key}, product n°{i + 1}"
