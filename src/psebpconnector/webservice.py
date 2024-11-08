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


from psebpconnector.exceptions import BadHTTPCode
from psebpconnector.models import Order, OrderPrinted, Product
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

    def _build_credentials(self) -> HTTPBasicAuth:
        return HTTPBasicAuth(self.apikey, '')

    def _build_url(self, endpoint: str, params: Optional[Dict[str, str]] = None):
        url = f"{self.url}/{endpoint}"
        if params:
            url += '?' + urlencode(params)
        return url

    def _do_api_call(self,
                     url: str,
                     expected_result_codes: List[int] = [200],
                     method: str = 'get',
                     data: Optional[dict] = None) -> Response:
        result = getattr(self._session, method)(url, data=data)

        if result.status_code not in expected_result_codes:
            raise BadHTTPCode(f"{method.upper()} {url}: Bad HTTP status code {result.status_code}")

        return result

    def get_order(self, order_id: int) -> Order:
        """
        :param order_id: ID of the order to be retrieved
        :return: An Order object representing the retrieved order
        """
        result = self._do_api_call(self._build_url(f"orders/{order_id}"))
        return Order.from_dict(result.json()['order'])

    def get_order_printed(self, order_printed_id: int) -> OrderPrinted:
        """
        :param order_printed_id: The unique identifier for the printed order.
        :return: An instance of the OrderPrinted class containing details of the printed order.
        """
        result = self._do_api_call(self._build_url(f"orders_printed/{order_printed_id}"))
        return OrderPrinted(**result.json()['order_printed'])

    def get_orders_to_export(self):
        """
        Fetches a list of orders that have been marked as printed but not yet exported, in a paginated manner.

        :return: A generator yielding orders that need to be exported
        """
        for i in range(self._MAX_CALLS):
            pagination_start = i * self._PAGINATION_SIZE
            pagination_stop = (i + 1) * self._PAGINATION_SIZE

            result = self._do_api_call(self._build_url('orders_printed', {
                'filter[exported]': '0',
                'limit': f"{pagination_start},{pagination_stop}"
            }))

            for order_printed_entry in result.json()['orders_printed']:
                order_printed = self.get_order_printed(order_printed_entry['id'])
                order = self.get_order(order_printed.id_order)
                yield order

    def get_product(self, product_id: int):
        result = self._do_api_call(self._build_url(f"products/{product_id}"))
        return Product.from_dict(result['product'])

    def test_api_authentication(self) -> bool:
        s = Session()
        response = s.get(self._build_url(''), auth=self._build_credentials())
        return response.status_code == 200
