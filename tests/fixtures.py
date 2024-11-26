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

from .datasets import *
from pathlib import Path
from psebpconnector.connector import Connector
from pytest import fixture


def get_address(_, address_id):
    return ADDRESSES[address_id]

def get_product(_, product_id):
    return PRODUCTS[product_id]

def get_countries_iso_code():
    return COUNTRIES

def get_currencies_iso_code():
    return CURRENCIES

@fixture
def offline_connector(request, mocker):
    orders = getattr(request, 'param', SINGLE_ORDER_WITH_TWO_PRODUCTS_BAD_AMOUNT)
    mocker.patch("psebpconnector.webservice.Webservice.get_countries_iso_code", side_effect=get_countries_iso_code)
    mocker.patch("psebpconnector.webservice.Webservice.get_currencies_iso_code", side_effect=get_currencies_iso_code)
    mocker.patch("psebpconnector.webservice.Webservice.get_orders_to_export", return_value=orders)
    mocker.patch("psebpconnector.webservice.Webservice.get_address", new=get_address)
    mocker.patch("psebpconnector.webservice.Webservice.get_product", new=get_product)
    mocker.patch("psebpconnector.webservice.Webservice.test_api_authentication", return_value=True)
    mocker.patch("psebpconnector.webservice.Webservice.set_order_exported")
    mocker.patch("psebpconnector.connector.Connector.import_files")
    connector = Connector(Path(__file__).parent / 'samples/config/config_file_ok.ini')
    return connector
