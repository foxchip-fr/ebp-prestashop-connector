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
from pathlib import Path
from psebpconnector.connector import Connector
from psebpconnector.export_models import ExportOrderRow, ExportProduct


EXPORTED_ORDERS = []
EXPORTED_PRODUCTS = []

EXPECTED_RESULTS = [
    (
        # Simple case
        SINGLE_ORDER_FR_ONE_PRODUCT,
        (
            [{
                'document_number': '123456',
                'document_number_suffix': '123456',
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
                'document_number': '123456',
                'document_number_suffix': '123456',
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
    ),
    (
        SINGLE_ORDER_REFUND,
        (
            [{
                'document_number': '12345611',
                'document_number_suffix': '12345611',
                'line_quantity': '-1',
                'line_vat_rate': '20.000000',
                'line_unit_price': '36.000000',
                'document_payment_method': 'FNAC',
                'document_shipping_cost_notax': '-6.250000',
                'document_currency_rate': '',
                'line_vat_code': '36cab0de-3e5b-4bee-a556-8eabb1673e76',
            }],
            [{
                'code': '4983164196146',
                'name': 'Figurine One Piece - Monkey.D.Luffy Battle Record Collection II 15cm',
                'type': 'BIEN',
                'price': '30.000000',
                'ean': '4983164196146',
                'wholesale_price': '19.350000',
            }]
        )
    )
]

EXPECTED_RESULTS_REFUNDS = [

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
def test_orders(offline_connector, mocker, should):
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

def test_orders_limit(offline_connector, mocker):
    global EXPORTED_ORDERS
    EXPORTED_ORDERS = []

    connector = Connector(Path(__file__).parent / 'samples/config/config_file_ok_limit_1.ini')
    mocker.patch("psebpconnector.webservice.Webservice.get_orders_to_export", return_value=SINGLE_ORDER_FR_ONE_PRODUCT*3)
    mocker.patch('psebpconnector.connector.Connector._write_csv_line', new=_fake_write_csv_line)
    assert connector.run() == 0
    assert len(EXPORTED_ORDERS) == 1

def test_orders_nolimit(offline_connector, mocker):
    global EXPORTED_ORDERS
    EXPORTED_ORDERS = []

    connector = Connector(Path(__file__).parent / 'samples/config/config_file_ok.ini')
    mocker.patch("psebpconnector.webservice.Webservice.get_orders_to_export", return_value=SINGLE_ORDER_FR_ONE_PRODUCT*3)
    mocker.patch('psebpconnector.connector.Connector._write_csv_line', new=_fake_write_csv_line)
    assert connector.run() == 0
    assert len(EXPORTED_ORDERS) == 3

def test_orders_semicolon(offline_connector, mocker):
    global EXPORTED_ORDERS
    EXPORTED_ORDERS = []

    connector = Connector(Path(__file__).parent / 'samples/config/config_file_ok.ini')
    mocker.patch("psebpconnector.webservice.Webservice.get_orders_to_export",
                 return_value=ORDER_WITH_SPECIAL_CHAR_IN_ADDRESS)
    mocker.patch('psebpconnector.connector.Connector._write_csv_line', new=_fake_write_csv_line)

    assert offline_connector.run() == 0
    assert len(EXPORTED_ORDERS) == 1
    order = EXPORTED_ORDERS[0]
    assert order.document_client_name == "DUPONT JEAN"
    assert order.document_invoice_address_1 == "1  Chemin"
    assert order.document_invoice_address_2 == "de  la ferme"
    assert order.document_invoice_zip_code == "12345"
    assert order.document_invoice_city == "VILLE"
    assert order.document_invoice_lastname == "DUPONT"
    assert order.document_invoice_firstname == "JEAN"
    assert order.document_delivery_address_1 == "1  Chemin"
    assert order.document_delivery_address_2 == "de  la ferme"
    assert order.document_delivery_city == "VILLE"
    assert order.document_delivery_lastname == "DUPONT"
    assert order.document_delivery_firstname == "JEAN"
