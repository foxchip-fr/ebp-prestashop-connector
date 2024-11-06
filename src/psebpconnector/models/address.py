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


class Address(Model):
    id: int
    id_customer: int = 0
    id_manufacturer: int = 0
    id_supplier: int = 0
    id_warehouse: int = 0
    id_country: int = 0
    id_state: int = 0
    alias: str = ''
    company: str = ''
    lastname: str = ''
    firstname: str = ''
    vat_number: int = 0
    address1: str = ''
    address2: str = ''
    postcode: str = ''
    city: str = ''
    other: str = ''
    phone: str = ''
    phone_mobile: str = ''
    dni: str = ''
    deleted: int = 0
    date_add: str = ''
    date_upd: str = ''
