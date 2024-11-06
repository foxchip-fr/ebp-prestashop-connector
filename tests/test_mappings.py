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


import json
from pathlib import Path

import pytest

from psebpconnector.connector import Connector
from psebpconnector.models import Order

ORDER_1 = Order.from_dict(json.loads('{"order":{"id":549085,"id_address_delivery":967452,"id_address_invoice":967452,"id_cart":817776,"id_currency":1,"id_lang":1,"id_customer":532822,"id_carrier":103,"current_state":4,"module":"feedbiz","invoice_number":541557,"invoice_date":"2024-07-05 19:40:27","delivery_number":528463,"delivery_date":"2024-07-08 10:52:56","valid":"1","date_add":"2024-07-05 16:40:18","date_upd":"2024-10-23 11:09:16","shipping_number":"885000009059824","id_shop_group":1,"id_shop":1,"secure_key":"f6e7751671880b23ba68281089d71d35","payment":"Amazon - FR","total_discounts":"0.000000","total_discounts_tax_incl":"0.000000","total_discounts_tax_excl":"0.000000","total_paid":"20.230000","total_paid_tax_incl":"20.230000","total_paid_tax_excl":"16.860000","total_paid_real":"40.460000","total_products":"9.780000","total_products_wt":"11.730000","total_shipping":"8.500000","total_shipping_tax_incl":"8.500000","total_shipping_tax_excl":"7.080000","carrier_tax_rate":"20.000","total_wrapping":"0.000000","total_wrapping_tax_incl":"0.000000","total_wrapping_tax_excl":"0.000000","round_mode":2,"round_type":2,"conversion_rate":"1.000000","reference":"FMHGOYBGK","associations":{"order_rows":[{"id":983222,"product_id":52695,"product_attribute_id":0,"product_quantity":1,"product_name":"Porte Clé Capitaine Flam - Professeur Simon Gomme 8cm","product_reference":"4589504961513","product_ean13":"4589504961513","product_isbn":"","product_upc":"","product_price":"9.775000","id_customization":0,"unit_price_tax_incl":"11.730000","unit_price_tax_excl":"9.775000"}]}}}')['order'])


def test_consistency_ok(mocker):
    connector = Connector(Path(__file__).parent / 'samples/config/config_file_ok.ini')
    connector.load_payment_method_mapping()
    connector.load_vat_mapping()
    connector.check_consistency()


def test_consistency_bad_territoriality(mocker):
    connector = Connector(Path(__file__).parent / 'samples/config/config_file_ok.ini')
    connector.payment_method_mapping = {'foo': { True: ('foo', 'bar', 'baz') }}
    connector.load_vat_mapping()
    with pytest.raises(AssertionError):
        connector.check_consistency()