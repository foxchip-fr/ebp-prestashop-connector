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


from datetime import datetime
from psebpconnector.exceptions import BadHTTPCode
from psebpconnector.models import *
from requests import Response, Session
from requests.auth import HTTPBasicAuth
from typing import Dict, List, Optional
from urllib.parse import urlencode


class Webservice:
    _PAGINATION_SIZE = 10
    _MAX_CALLS = 1000

    def __init__(self, url: str, apikey: str):
        """
        :param url: The base URL for the API endpoint.
        :param apikey: The API key used for authenticating requests.
        """
        self.url = url.rstrip('/')
        self.apikey = apikey

        self._session = Session()
        self._session.auth = self._build_credentials()
        self._session.headers = {
            'Content-Type': 'application/json',
            'Io-Format': 'JSON',
        }

        self.order_error_counter = 0
        self.refund_error_counter = 0

    def _build_credentials(self) -> HTTPBasicAuth:
        return HTTPBasicAuth(self.apikey, '')

    def _build_url(self, endpoint: str, params: Optional[Dict[str, str]] = None):
        url = f"{self.url}/{endpoint}"
        if params:
            url += '?' + urlencode(params, safe=':+')
        return url

    def _do_api_call(self,
                     url: str,
                     expected_result_codes: List[int] = [200],
                     method: str = 'get',
                     data: Optional[dict] = None) -> Response:
        result = getattr(self._session, method)(url, data=data)

        if result.status_code not in expected_result_codes:
            raise BadHTTPCode(f"{method.upper()} {url}: Bad HTTP status code {result.status_code}\n{result.text}")

        return result

    def _set_order_exported_field(self, order: Order, field_value: int):
        order_printed = self.get_order_printed(order.id)

        patch_xml = f"""<?xml version="1.0" encoding="UTF-8"?>
        <prestashop xmlns:xlink="http://www.w3.org/1999/xlink">
          <order_printed>
            <id><![CDATA[{order_printed.id}]]></id>
            <exported><![CDATA[{field_value}]]></exported>
            <exported_date><![CDATA[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}]]></exported_date>
          </order_printed>
        </prestashop>"""

        self._do_api_call(self._build_url(f"orders_printed/{order_printed.id_order}"), method='patch', data=patch_xml)

    def get_address(self, address_id: int) -> Address:
        result = self._do_api_call(self._build_url(f"addresses/{address_id}"))
        return Address.from_dict(result.json()['address'])

    def get_countries_iso_code(self) -> Dict[int, str]:
        result = self._do_api_call(self._build_url('countries', {
            'filter[active]': '1',
            'display': '[id,iso_code]',
        }))
        return {country['id']: country['iso_code'] for country in result.json()['countries']}

    def get_currencies_iso_code(self) -> Dict[int, str]:
        result = self._do_api_call(self._build_url('currencies', {
            'filter[active]': '1',
            'display': '[id,iso_code]',
        }))
        return {currency['id']: currency['iso_code'] for currency in result.json()['currencies']}

    def get_order(self, order_id: int) -> Order:
        """
        :param order_id: ID of the order to be retrieved
        :return: An Order object representing the retrieved order
        """
        result = self._do_api_call(self._build_url(f"orders/{order_id}"))
        return Order.from_dict(result.json()['order'])

    def get_order_printed(self, order_id: int) -> OrderPrinted:
        """
        :param order_id: The unique identifier of the order
        :return: An instance of the OrderPrinted class containing details of the printed order.
        """
        result = self._do_api_call(self._build_url(f"orders_printed", {
            'filter[id_order]': f"{order_id}",
        }))
        id_order_printed = result.json()['orders_printed'][0]['id']
        result = self._do_api_call(self._build_url(f"orders_printed/{id_order_printed}"))
        return OrderPrinted(**result.json()['order_printed'])

    def get_orders_to_export(self, valid_orders_status: List[str], refund_orders_status: List[str]):
        """
        Fetches a list of orders that have been marked as printed but not yet exported, in a paginated manner.

        :return: A generator yielding orders that need to be exported
        """

        exporting_regular_orders = True
        exporting_refunds = False
        for i in range(self._MAX_CALLS):
            if exporting_regular_orders:
                result = self._do_api_call(self._build_url('orders_with_printed', {
                    'filter[orders_printed][exported]': '0',
                    'filter[current_state]': '[' + '|'.join(valid_orders_status) + ']',
                    'sort': '[id_ASC]',
                    'limit': f"{self.order_error_counter},{self.order_error_counter + self._PAGINATION_SIZE}"
                }))
            elif exporting_refunds:
                result = self._do_api_call(self._build_url('orders_with_printed', {
                    'filter[orders_printed][exported]': '1',
                    'filter[current_state]': '[' + '|'.join(refund_orders_status) + ']',
                    'sort': '[id_ASC]',
                    'limit': f"{self.refund_error_counter},{self.refund_error_counter + self._PAGINATION_SIZE}"
                }))
            else:
                break

            orders_list = result.json()

            if orders_list:
                for order_entry in result.json()['orders']:
                    order = self.get_order(order_entry['id'])
                    order.is_refund = exporting_refunds
                    yield order
            else:
                if exporting_regular_orders:
                    exporting_regular_orders = False
                    exporting_refunds = True
                else:
                    exporting_refunds = False


    def get_product(self, product_id: int):
        result = self._do_api_call(self._build_url(f"products/{product_id}"))
        return Product.from_dict(result.json()['product'])

    def set_order_exported(self, order: Order):
        self._set_order_exported_field(order, 1)

    def set_order_refund(self, order:Order):
        self._set_order_exported_field(order, 2)

    def test_api_authentication(self) -> bool:
        s = Session()
        response = s.get(self._build_url(''), auth=self._build_credentials())
        return response.status_code == 200
