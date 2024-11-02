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


from configparser import NoOptionError
from pathlib import Path
from psebpconnector.connector_configuration import ConnectorConfiguration


def test_configuration_with_bad_syntax():
    with pytest.raises(ValueError):
        ConnectorConfiguration(Path(__file__).parent / 'samples/config/config_file_with_bad_syntax.ini')


def test_configuration_missing_keys():
    with pytest.raises(NoOptionError):
        ConnectorConfiguration(Path(__file__).parent / 'samples/config/config_file_with_missing_keys.ini')


def test_configuration_valid_file():
    c = ConnectorConfiguration(Path(__file__).parent / 'samples/config/config_file_ok.ini')
    assert c.url
    assert c.apikey
    assert c.ebp_executable_path
