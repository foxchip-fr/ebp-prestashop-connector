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


from configparser import ConfigParser, Error
from pathlib import Path
from typing import List


class ConnectorConfiguration:
    _config: ConfigParser
    url: str
    apikey: str
    ebp_executable_path: Path
    order_valid_status: List[str]
    payment_method_mapping_file_path: Path
    vat_mapping_file_path: Path
    working_directory: Path
    ebp_articles_config_name: str = 'foxchip_ebp_connector'
    ebp_orders_config_name: str = 'foxchip_ebp_connector'
    ebp_database_path: Path
    o365_client_id = None
    o365_email = None
    o365_secret = None
    o365_tenant_id = None

    def __init__(self, config_path: Path):
        self._read_configuration(config_path)
        self.load_required_options()

        if not self.ebp_executable_path.is_file():
            raise FileNotFoundError(f"The file {self.ebp_executable_path} does not exists.")

    def _read_configuration(self, config_path):
        if not config_path.is_file():
            raise FileNotFoundError(f"The file {config_path} does not exist.")

        self._config = ConfigParser()

        try:
            self._config.read(config_path)
        except Error as e:
            raise ValueError(f"Error reading the configuration file: {e}")

    def load_required_options(self):
        for key in ['url',
                    'apikey',
                    'ebp_executable_path',
                    'ebp_database_path',
                    'order_valid_status',
                    'order_refund_status',
                    'payment_method_mapping_file_path',
                    'vat_mapping_file_path',
                    'working_directory',]:
            setattr(self, key, self._config.get('main', key))
        self.ebp_executable_path = Path(self.ebp_executable_path)
        self.order_valid_status = [status.strip() for status in self.order_valid_status.split(',')]
        self.payment_method_mapping_file_path = Path(self.payment_method_mapping_file_path)
        self.vat_mapping_file_path = Path(self.vat_mapping_file_path)
        self.working_directory = Path(self.working_directory)

        if self._config.has_section ('o365'):
            for key in ['client_id', 'email', 'secret', 'tenant_id']:
                setattr(self, f"o365_{key}", self._config.get('o365', key))
