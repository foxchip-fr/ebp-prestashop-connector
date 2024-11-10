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


import csv
import time

from psebpconnector.connector_configuration import ConnectorConfiguration
from psebpconnector.webservice import Webservice
from pathlib import Path


class Connector:
    def __init__(self, config_path: Path):
        """
        New Connector object

        :param config_path: The path to the configuration file.
        :raises:
            FileNotFoundError: If the configuration file does not exist at the given path.
            ValueError: If there is an error reading the configuration file.
        """
        self.config = ConnectorConfiguration(config_path)
        self._startup_time = time.time()
        self._csv_products_path = Path(self.config.working_directory / f"articles_{self._startup_time}.csv")
        self._csv_products_file = open(self._csv_products_path, 'w')
        self.csv_products = csv.writer(self._csv_products_file, delimiter=';', quotechar='"')
        self._csv_orders_path = Path(self.config.working_directory / f"orders_{self._startup_time}.csv")
        self._csv_orders_file = open(self._csv_orders_path, 'w')
        self.csv_orders = csv.writer(self._csv_orders_file, delimiter=';', quotechar='"')
        self.exported_products = set()
        self.webservice = Webservice(self.config.url, self.config.apikey)

        """
            Payment Method Mapping
            ----------------------
            <Prestashop payment method field>:
                <VAT applied to order (bool)>: (<ebp_client_code>, <currency>, <territoriality>)
        """
        self.payment_method_mapping = {}

        """
            VAT Mapping
            -----------
            <territoriality>:
                <country_id>: (<vat_value>,<ebp_vat_id>)
        """
        self.vat_mapping = {}

    def _check_territoriality_consistency(self):
        for payment_method in self.payment_method_mapping:
            for has_vat in self.payment_method_mapping[payment_method]:
                territoriality = self.payment_method_mapping[payment_method][has_vat][2]
                assert territoriality in self.vat_mapping, f"Territoriality '{territoriality}' not found in VAT mapping file"

    def _write_product_line(self, product):
        """ write a line in the products CSV
        :param product: Product to import in EBP

            CSV ROWS:
            - product code (EAN)
            - Name
            - Type
            - Price (WT)
            - EAN
        """
        self.csv_products.writerow([
            product.ean13,
            product.name,
            'BIEN',
            product.price,
            product.ean13,
        ])

    def check_consistency(self):
        self._check_territoriality_consistency()

    def export_product(self, product_id: int):
        if product_id not in self.exported_products:
            product = self.webservice.get_product(product_id)
            self._write_product_line(product)
            self.exported_products.add(product_id)

    def export_orders_and_products(self):
        for order in self.webservice.get_orders_to_export():
            vat_applied = float(order.total_products_wt) - float(order.total_products) > 0
            try:
                ebp_client_code, currency, territoriality = self.payment_method_mapping[order.payment][vat_applied]
                address = self.webservice.get_address(order.id_address_delivery)
                vat_value, ebp_vat_id = self.vat_mapping[territoriality][address.id_country]

                # Get products
                for order_row in order.associations['order_rows']:
                    if order_row['product_id'] == 0:
                        raise ValueError(order_row['product_id'])
                    self.export_product(order_row['product_id'])
                print(ebp_client_code, currency, territoriality, ebp_vat_id, vat_value)
            except KeyError:
                # TODO Log an error
                print('Error with order ', order)
                continue

    def load_payment_method_mapping(self):
        with open(self.config.payment_method_mapping_file_path, 'r') as f:
            reader = csv.reader(f, delimiter=';')
            next(reader, None)  # Skip header

            line_number = 2
            for rows in reader:
                if rows:
                    if len(rows) != 5:
                        raise ValueError(f"{self.config.payment_method_mapping_file_path.name}, l.{line_number}: expected 5 columns")
                    payment_method, with_vat, client_code, currency, territoriality = rows
                    with_vat = with_vat == 'AVEC'
                    self.payment_method_mapping.setdefault(payment_method.strip(), {})
                    self.payment_method_mapping[payment_method.strip()][with_vat] = (client_code.strip(), currency.strip(), territoriality.strip())

    def load_vat_mapping(self):
        with open(self.config.vat_mapping_file_path, 'r') as f:
            reader = csv.reader(f, delimiter=';')
            next(reader, None)  # Skip header

            line_number = 2
            for rows in reader:
                if rows:
                    if len(rows) != 12:
                        raise ValueError(f"{self.config.vat_mapping_file_path.name}, l.{line_number}: expected 12 columns")
                    territoriality, vat, ebp_id, ps_country_id = rows[0], rows[2], rows[10], int(rows[11])
                    self.vat_mapping.setdefault(territoriality, {})

                    # EXONERATION
                    vat = 0.0 if ps_country_id == -1 else float(vat.replace(',','.'))

                    self.vat_mapping[territoriality][ps_country_id] = (vat, ebp_id)
                line_number += 1

    def run(self):
        self.load_payment_method_mapping()
        self.load_vat_mapping()
        self.check_consistency()
        assert self.webservice.test_api_authentication(), "Unable to login"
        self.export_orders_and_products()
