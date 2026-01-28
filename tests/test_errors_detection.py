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

from .datasets import SINGLE_ORDER_WITH_TWO_PRODUCTS_BAD_AMOUNT, SINGLE_ORDER_WITH_UNKNOWN_PAYMENT_METHOD
from .fixtures import offline_connector
from pathlib import Path


@pytest.mark.parametrize("offline_connector", [SINGLE_ORDER_WITH_TWO_PRODUCTS_BAD_AMOUNT], indirect=True)
def test_logger_no_error(offline_connector):
    assert offline_connector.run() == 0
    assert not offline_connector.errors_logged()

@pytest.mark.parametrize("offline_connector", [SINGLE_ORDER_WITH_UNKNOWN_PAYMENT_METHOD], indirect=True)
def test_logger_with_error(offline_connector):
    assert offline_connector.run() == 0
    assert offline_connector.errors_logged()

@pytest.mark.parametrize("offline_connector", [SINGLE_ORDER_WITH_TWO_PRODUCTS_BAD_AMOUNT], indirect=True)
@pytest.mark.parametrize("logfile", ["ebp_no_order_imported.txt", "ebp_order_import_ok.txt"])
def test_ebp_order_import_ok(offline_connector, logfile):
    offline_connector._ebp_import_orders_logs_path = offline_connector._ebp_import_products_logs_path = (Path('tests/samples/logs') / logfile)
    assert not offline_connector.errors_raised_by_ebp()

@pytest.mark.parametrize("logfile", ["ebp_no_order_imported.txt", "ebp_order_import_ok.txt"])
def test_ebp_order_import_ok(offline_connector, logfile):
    offline_connector._ebp_import_orders_logs_path = offline_connector._ebp_import_products_logs_path = (Path('tests/samples/logs') / logfile)
    assert not offline_connector.errors_raised_by_ebp()

@pytest.mark.parametrize("logfile", ["ebp_order_import_ko.txt"])
def test_ebp_order_import_ok(offline_connector, logfile):
    offline_connector._ebp_import_orders_logs_path = offline_connector._ebp_import_products_logs_path = (Path('tests/samples/logs') / logfile)
    assert offline_connector.errors_raised_by_ebp()

@pytest.mark.parametrize("logfile", ["ebp_malformed_message_1.txt"])
def test_ebp_ebp_malformed_message_1(offline_connector, logfile):
    offline_connector._ebp_import_orders_logs_path = offline_connector._ebp_import_products_logs_path = (Path('tests/samples/logs') / logfile)
    assert not offline_connector.errors_raised_by_ebp()

@pytest.mark.parametrize("logfile", ["ebp_malformed_message_2.txt"])
def test_ebp_ebp_malformed_message_2(offline_connector, logfile):
    offline_connector._ebp_import_orders_logs_path = offline_connector._ebp_import_products_logs_path = (Path('tests/samples/logs') / logfile)
    assert not offline_connector.errors_raised_by_ebp()

@pytest.mark.parametrize("logfile", ["ebp_malformed_message_3.txt"])
def test_ebp_ebp_malformed_message_3(offline_connector, logfile):
    offline_connector._ebp_import_orders_logs_path = offline_connector._ebp_import_products_logs_path = (Path('tests/samples/logs') / logfile)
    assert offline_connector.errors_raised_by_ebp()
