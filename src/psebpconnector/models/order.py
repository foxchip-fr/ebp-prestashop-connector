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

from psebpconnector.models.model import Model
from dataclasses import dataclass
from typing import Any, Optional


@dataclass
class Order(Model):
    id: int
    id_address_delivery: int = 0
    id_address_invoice: int = 0
    id_cart: int = 0
    id_currency: int = 0
    id_lang: int = 0
    id_customer: int = 0
    id_carrier: int = 0
    id_shop_group: int = 0
    id_shop: int = 0
    is_refund: bool = False
    associations: Optional[dict] = None
    date_add: str = ""
    conversion_rate: float = 1
    current_state: int = 0
    delivery_date: str = ''
    delivery_number: str = ''
    invoice_date: str = ''
    invoice_number: str = ''
    module: str = ''
    payment: str = ''
    reference: str = ''
    shipping_number: str = ''
    total_discounts: float = 0
    total_paid: float = 0
    total_paid_real: float = 0
    total_products: float = 0
    total_products_wt: float = 0
    total_shipping: float = 0
    total_shipping_tax_incl: float = 0
    total_shipping_tax_excl: float = 0
