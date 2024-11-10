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


from pathlib import Path
from psebpconnector.connector import Connector


def test_consistency_ok():
    connector = Connector(Path(__file__).parent / 'samples/config/config_file_ok.ini')
    connector.load_payment_method_mapping()
    connector.load_vat_mapping()
    connector.check_consistency()


def test_consistency_bad_territoriality():
    connector = Connector(Path(__file__).parent / 'samples/config/config_file_ok.ini')
    connector.payment_method_mapping = {'foo': { True: ('foo', 'bar', 'baz') }}
    connector.load_vat_mapping()
    with pytest.raises(AssertionError):
        connector.check_consistency()