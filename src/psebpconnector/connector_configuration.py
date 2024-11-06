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


class ConnectorConfiguration:
    _config: ConfigParser
    url: str
    apikey: str
    ebp_executable_path: Path
    payment_method_mapping_file_path: Path
    vat_mapping_file_path: Path

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
        for key in ['url', 'apikey', 'ebp_executable_path', 'payment_method_mapping_file_path', 'vat_mapping_file_path']:
            setattr(self, key, self._config.get('main', key))
        self.ebp_executable_path = Path(self.ebp_executable_path)
        self.payment_method_mapping_file_path = Path(self.payment_method_mapping_file_path)
        self.vat_mapping_file_path = Path(self.vat_mapping_file_path)