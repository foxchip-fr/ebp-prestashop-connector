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
import logging
import subprocess
import sys
import time

from dataclasses import asdict
from datetime import datetime
from psebpconnector.connector_configuration import ConnectorConfiguration
from psebpconnector.dummy_handler import DummyHandler
from psebpconnector.exceptions import BadHTTPCode, InvalidOrder
from psebpconnector.export_models import ExportOrderRow, ExportProduct
from psebpconnector.mailer import Mailer
from psebpconnector.models import Order, OrderRow, Address
from psebpconnector.webservice import Webservice
from pathlib import Path


class Connector:
    VAT_MAPPING_EXONERATION_ID = -1

    def __init__(self, config_path: Path):
        """
        New Connector object

        :param config_path: The path to the configuration file.
        :raises:
            FileNotFoundError: If the configuration file does not exist at the given path.
            ValueError: If there is an error reading the configuration file.
        """
        self.countries_iso_code = {}
        self.currencies_iso_code = {}
        self._startup_time = time.time()
        self.config = ConnectorConfiguration(config_path)
        self._logs_file_path = Path(self.config.working_directory / f"logs_{self._startup_time}.txt")
        self._setup_logger()
        self._csv_products_path = Path(self.config.working_directory / f"articles_{self._startup_time}.csv")
        self._csv_products_file = open(self._csv_products_path, 'w', encoding='utf-8-sig', newline='')
        self.csv_products = csv.writer(self._csv_products_file, delimiter=';', quotechar='"')
        self._csv_orders_path = Path(self.config.working_directory / f"orders_{self._startup_time}.csv")
        self._csv_orders_file = open(self._csv_orders_path, 'w', encoding='utf-8-sig', newline='')
        self.csv_orders = csv.writer(self._csv_orders_file, delimiter=';', quotechar='"')
        self.exported_products = set()
        self.webservice = Webservice(self.config.url, self.config.apikey)
        self._ebp_import_products_logs_path = self.config.working_directory / f"ebp_import_products_logs_{self._startup_time}.txt"
        self._ebp_import_orders_logs_path = self.config.working_directory / f"ebp_import_orders_logs_{self._startup_time}.txt"

        if self.config.o365_email:
            self.mailer = Mailer(self.config.o365_client_id,
                                 self.config.o365_secret,
                                 self.config.o365_tenant_id,
                                 self.config.o365_email)
        else:
            self.mailer = None


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

    def _check_if_vat_applied(self, order):
        """ Check if VAT has been applied to this order by looking at the difference between the total order price
            and the total order price without VAT.
        """
        vat_applied = float(order.total_products_wt) - float(order.total_products) > 0
        self.logger.debug(f"Order {order.id}: total_products_wt: {order.total_products_wt}, "
                          f"total_products: {order.total_products}, "
                          f"VAT applied: {vat_applied}")
        return vat_applied

    def _check_territoriality_consistency(self):
        for payment_method in self.payment_method_mapping:
            for has_vat in self.payment_method_mapping[payment_method]:
                territoriality = self.payment_method_mapping[payment_method][has_vat][2]
                assert territoriality in self.vat_mapping, f"Territoriality '{territoriality}' not found in VAT mapping file"

    @staticmethod
    def _compute_order_total(order, order_rows, vat_value):
        total = 0.0
        for order_row in order_rows:
            total += float(order_row.unit_price_tax_excl) * int(order_row.product_quantity)
        total += float(order.total_shipping_tax_excl)
        return total * (1 + vat_value)

    def _get_country_iso_code(self, country_id):
        if country_id not in self.countries_iso_code:
            self.logger.error(f"Unable to find country iso code for country_id {country_id}")
            raise InvalidOrder
        return self.countries_iso_code[country_id]

    def _get_currency_iso_code(self, currency_id):
        if currency_id not in self.currencies_iso_code:
            self.logger.error(f"Unable to find currency iso code for country_id {currency_id}")
            raise InvalidOrder
        return self.currencies_iso_code[currency_id]

    def _get_info_from_payment_method(self, order, vat_applied):
        try:
            ebp_client_code, currency, territoriality, ebp_payment_method = self.payment_method_mapping[order.payment][vat_applied]
        except KeyError:
            self.logger.error(f"Order {order.id}: no payment method found for {order.payment}, with_vat: {vat_applied}, "
                              f"skipping order {order.id}")
            raise InvalidOrder
        self.logger.debug(f"Order {order.id}: ebp_client_code: {ebp_client_code}, "
                          f"currency: {currency}, "
                          f"territoriality: {territoriality}, "
                          f"ebp_payment_method: {ebp_payment_method}")
        return ebp_client_code, currency, territoriality, ebp_payment_method

    def _get_order_delivery_address(self, order):
        try:
            address = self.webservice.get_address(order.id_address_delivery)
        except BadHTTPCode as e:
            self.logger.error(f"Order {order.id}: error while trying to retrieve delivery address (ID "
                              f"{order.id_address_delivery}) - {e}")
            raise InvalidOrder
        self.logger.debug(f"Order {order.id}: found delivery address {address}")
        return address

    def _get_order_invoice_address(self, order):
        try:
            address = self.webservice.get_address(order.id_address_invoice)
        except BadHTTPCode as e:
            self.logger.error(f"Order {order.id}: error while trying to retrieve invoice address (ID "
                              f"{order.id_address_invoice}) - {e}")
            raise InvalidOrder
        self.logger.debug(f"Order {order.id}: found invoice address {address}")
        return address

    def _get_order_rows(self, order):
        if (not isinstance(order.associations, dict)
                or 'order_rows' not in order.associations
                or len(order.associations['order_rows']) == 0):
            self.logger.error(f"Order {order.id}: no product found for this order")
            raise InvalidOrder

        rows = []
        try:
            for order_row_entry in order.associations['order_rows']:
                order_row = OrderRow.from_dict(order_row_entry)
                self.logger.debug(f"Order {order.id}: has order row {order_row}")
                if order_row.product_id == 0:
                    self.logger.error(f"Order {order.id}: invalid product_id {order_row_entry['product_id']}, skipping")
                    raise InvalidOrder
                rows.append(order_row)
        except (KeyError, TypeError) as e:
            self.logger.error(f"Order {order.id}: malformed order rows - {order.associations}, {e}")
            raise InvalidOrder
        return rows

    def _get_order_vat(self, order, territoriality, ps_country_id, vat_applied):
        """ Get VAT rate and VAT EBP ID by looking in the mapping VAT_MAPPING file
            :param order: current order
            :param territoriality: territoriality guessed from payment method
            :param ps_country_id: Prestashop country ID of the delivery address
        """
        if territoriality not in self.vat_mapping:
            self.logger.error(f"Order {order.id}: territoriality '{territoriality}' not found in VAT mapping file")
            raise InvalidOrder

        if vat_applied:
            if ps_country_id not in self.vat_mapping[territoriality]:
                self.logger.error(f"Order {order.id}: country ID '{ps_country_id}' ({self._get_country_iso_code(ps_country_id)}) not found in VAT mapping file for "
                                  f"territoriality '{territoriality}'")
                raise InvalidOrder
            vat_value, ebp_vat_id = self.vat_mapping[territoriality][ps_country_id]
        else:
            if self.VAT_MAPPING_EXONERATION_ID not in self.vat_mapping[territoriality]:
                self.logger.warning(f"Order {order.id}: VAT_MAPPING_EXONERATION_ID ({self.VAT_MAPPING_EXONERATION_ID}) "
                                    f"not found in VAT mapping file for territoriality {territoriality}")
                raise InvalidOrder
            vat_value, ebp_vat_id = self.vat_mapping[territoriality][self.VAT_MAPPING_EXONERATION_ID]

        self.logger.debug(f"Order {order.id}: vat_value={vat_value}, ebp_vat_id={ebp_vat_id}")
        return vat_value, ebp_vat_id

    def _process_order(self, order):
        self.logger.debug(order)
        vat_applied = self._check_if_vat_applied(order)
        ebp_client_code, currency, territoriality, ebp_payment_method = self._get_info_from_payment_method(order, vat_applied)
        delivery_address = self._get_order_delivery_address(order)
        invoice_address = self._get_order_invoice_address(order)
        vat_value, ebp_vat_id = self._get_order_vat(order, territoriality, delivery_address.id_country, vat_applied)
        order_rows = self._get_order_rows(order)
        for order_row in order_rows:
            self.export_product(order_row.product_id)
            self.export_order_row(order, order_row, delivery_address, invoice_address, ebp_vat_id,
                                  ebp_client_code, ebp_payment_method, territoriality, vat_value)
            if order.is_refund:
                self.webservice.set_order_refund(order)
            else:
                self.webservice.set_order_exported(order)

    def _setup_logger(self):
        logger = logging.getLogger('ps_ebp_connector')
        logger.setLevel(logging.DEBUG)

        # STDOUT logs
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(logging.Formatter('ps_ebp_connector - [%(levelname)s] %(message)s'))
        handler.setLevel(logging.DEBUG)
        handler.addFilter(lambda record: record.levelno <= logging.INFO)
        logger.addHandler(handler)

        # STDERR logs
        handler = logging.StreamHandler(sys.stderr)
        handler.setFormatter(logging.Formatter('ps_ebp_connector - [%(levelname)s] %(message)s'))
        handler.setLevel(logging.WARNING)
        logger.addHandler(handler)

        handler = logging.FileHandler(self._logs_file_path)
        handler.setFormatter(logging.Formatter('%(asctime)s %(levelname)s %(message)s'))
        handler.setLevel(logging.DEBUG)
        logger.addHandler(handler)

        handler = DummyHandler()
        handler.setLevel(logging.WARNING)
        logger.addHandler(handler)

        self.logger = logger

    @staticmethod
    def _write_csv_line(obj, spamwriter):
        """write a line in a CSV using a dataclass as input"""
        spamwriter.writerow(list(asdict(obj).values()))

    def check_consistency(self):
        self._check_territoriality_consistency()

    def errors_logged(self):
        return self.logger.handlers[3].log_emitted

    def errors_raised_by_ebp(self):
        return 'erreur' in self._ebp_import_orders_logs_path.read_text().lower() or 'erreur' in self._ebp_import_products_logs_path.read_text().lower()

    def export_order_row(self,
                         order: Order,
                         order_row: OrderRow,
                         delivery_address: Address,
                         invoice_address: Address,
                         ebp_vat_id: str,
                         ebp_client_code: str,
                         ebp_payment_method: str,
                         ebp_territoriality: str,
                         vat_rate: float):
        export_order_row = ExportOrderRow(
            document_use_original_number='N',
            document_number_prefix='V',
            document_number_suffix=f"{order.id}",
            document_number=f"{order.id}",
            document_date=datetime.now().strftime('%d/%m/%Y'),
            document_client_code=ebp_client_code,
            document_civil='',
            document_client_name=f"{invoice_address.lastname.upper()} {invoice_address.firstname.upper()}",
            document_invoice_address_1=f"{invoice_address.address1}",
            document_invoice_address_2=f"{invoice_address.address2}",
            document_invoice_address_3='',
            document_invoice_address_4='',
            document_invoice_zip_code=f"{invoice_address.postcode}",
            document_invoice_city=f"{invoice_address.city}",
            document_invoice_department='',
            document_invoice_country_iso_code=self._get_country_iso_code(invoice_address.id_country),
            document_invoice_lastname=f"{invoice_address.lastname.upper()}",
            document_invoice_firstname=f"{invoice_address.firstname.upper()}",
            document_invoice_phone=f"{invoice_address.phone}",
            document_invoice_mobile_phone=f"{invoice_address.phone_mobile}",
            document_invoice_fax='',
            document_invoice_email='nomail@nomail.fr',
            document_delivery_address_1=f"{delivery_address.address1}",
            document_delivery_address_2=f"{delivery_address.address2}",
            document_delivery_address_3='',
            document_delivery_address_4='',
            document_delivery_zip_code=f"{delivery_address.postcode}",
            document_delivery_city=f"{delivery_address.city}",
            document_delivery_department='',
            document_delivery_country_iso_code=self._get_country_iso_code(delivery_address.id_country),
            document_delivery_lastname=f"{delivery_address.lastname.upper()}",
            document_delivery_firstname=f"{delivery_address.firstname.upper()}",
            document_delivery_phone=f"{delivery_address.phone}",
            document_delivery_mobile_phone=f"{delivery_address.phone_mobile}",
            document_delivery_fax='',
            document_delivery_email='nomail@nomail.fr',
            document_territoriality=ebp_territoriality,
            document_vat_number=f"{invoice_address.vat_number}",
            document_discount_pct=f"{round((float(order.total_discount) / (float(order.total_products_wt) + float(order.total_shipping))) / float(order.conversion_rate), 6):06f}",
            document_discount_amount=f"{order.total_discount}",
            document_escompte_pct='',
            document_escompte_amount='',
            document_shipping_cost_code='',
            document_shipping_cost_notax=f"{round((float(order.total_shipping) / (1 + vat_rate)) / float(order.conversion_rate), 6):06f}",
            document_shipping_cost_vat_rate=f"{round(vat_rate * 100, 6)}",
            document_shipping_tva_code=f"{ebp_vat_id}",
            document_total_notax='',
            document_total=f"{round((float(order.total_products_wt) + float(order.total_shipping) / float(order.conversion_rate)), 6):06f}",
            document_notes=f"Commande importée n°{order.id} - {order.reference}",
            line_product_code=f"{order_row.product_ean13}",
            line_description=f"{order_row.product_name}",
            line_quantity=f"{order_row.product_quantity}",
            line_vat_rate=f"{round(vat_rate * 100, 6):06f}",
            line_vat_code=f"{ebp_vat_id}",
            document_commercial_code='',
            line_unit_price_notax='',
            line_unit_price=f"{round((float(order_row.unit_price_tax_incl) / float(order.conversion_rate)), 6):06f}",
            line_discount_pct='0',
            line_discount_notax='0',
            line_price_notax='',
            line_price='',
            line_commercial_code='',
            document_payment_method=f"{ebp_payment_method}",
            deposit_amount='',
            deposit_payment_method='',
            deposit_date='',
            document_ignore_prices='0',
            document_name_delivery_address=f"{delivery_address.lastname.upper()} {delivery_address.firstname.upper()}",
            document_depot='',
            document_currency_rate=f"{round(float(order.conversion_rate), 6):06f}" if float(order.conversion_rate) != 1.0 else '',
            document_currency_iso_code=f"{self._get_currency_iso_code(order.id_currency)}" if float(order.conversion_rate) != 1.0 else '',
            deposit_amount_currency='',
            deposit_currency_rate='',
            deposit_currency_iso_code='',
            document_currency_amount=f"{round(float(order.total_products_wt) + float(order.total_shipping), 6):06f}" if float(order.conversion_rate) != 1.0 else '',
            document_currency_amount_notax='',
            document_currency_amount_shipping_notax=f"{round(float(order.total_shipping) / (1 + vat_rate), 6):06f}" if float(order.conversion_rate) != 1.0 else '',
            line_currency_unit_price_notax=f"{round(float(order_row.product_price) / (1 + vat_rate), 6):06f}" if float(order.conversion_rate) != 1.0 else '',
            line_currency_cumulative_discount_amount_notax='',
            line_currency_total_notax='',
            document_currency_used='T' if float(order.conversion_rate) != 1.0 else 'P',
            document_series='',
            document_business_code='',
            mroad_id='',
            mroad_technicality='',
            document_client_order_number='',
            line_ignore_linked_products='',
            document_language='')
        if order.is_refund:
            export_order_row.document_total = f"-{export_order_row.document_total}"
            export_order_row.line_quantity = f"-{export_order_row.line_quantity}"
            export_order_row.document_shipping_cost_notax = f"-{export_order_row.document_shipping_cost_notax}"
            if export_order_row.document_currency_amount_shipping_notax:
                export_order_row.document_currency_amount_shipping_notax = f"-{export_order_row.document_currency_amount_shipping_notax}"
            export_order_row.document_number_suffix += "11"
            export_order_row.document_number += "11"
        self.logger.debug(f"Order {order.id}, export_order_row: {export_order_row}")
        self._write_csv_line(export_order_row, self.csv_orders)

    def export_product(self, product_id: int):
        if product_id not in self.exported_products:
            self.logger.info(f"Exporting product {product_id}")
            product = self.webservice.get_product(product_id)
            export_product = ExportProduct(
                code=product.ean13,
                name=product.name[0]['value'],
                type='BIEN',
                price=f"{float(product.price):06f}",
                wholesale_price=f"{float(product.wholesale_price):06f}",
                ean=product.ean13)
            self.logger.debug(f"{export_product}")
            self._write_csv_line(export_product, self.csv_products)
            self.exported_products.add(product_id)

    def export_orders_and_products(self):
        exported_orders_counter = 0
        for order in self.webservice.get_orders_to_export(self.config.order_valid_status, self.config.order_refund_status):
            if self.config.order_limit and exported_orders_counter >= self.config.order_limit:
                break
            try:
                self._process_order(order)
            except InvalidOrder:
                self.logger.warning(f"Skipping order {order.id}")
            finally:
                exported_orders_counter += 1

    def import_files(self):
        self._csv_products_file.close()
        self._csv_orders_file.close()

        import_products_command = [
            str(self.config.ebp_executable_path),
            '/Gui=false;' + str(self._ebp_import_products_logs_path),
            '/Database=' + str(self.config.ebp_database_path) + ';EBPSDK',
            '/Import=' + str(self._csv_products_path) + ';Items;' + self.config.ebp_articles_config_name
        ]

        import_orders_command = [
            str(self.config.ebp_executable_path),
            '/Gui=false;' + str(self._ebp_import_orders_logs_path),
            '/Database=' + str(self.config.ebp_database_path) + ';EBPSDK',
            '/Import=' + str(self._csv_orders_path) + ';SaleInvoices;' + self.config.ebp_orders_config_name
        ]

        self.logger.info('Importing products')
        self.logger.debug(f"Subprocess args: {import_products_command}")
        subprocess.run(import_products_command)

        self.logger.info('Importing orders')
        self.logger.debug(f"Subprocess args: {import_orders_command}")
        subprocess.run(import_orders_command)

    def load_payment_method_mapping(self):
        with open(self.config.payment_method_mapping_file_path, 'r') as f:
            reader = csv.reader(f, delimiter=';')
            next(reader, None)  # Skip header

            line_number = 2
            for rows in reader:
                if rows:
                    if len(rows) != 6:
                        raise ValueError(f"{self.config.payment_method_mapping_file_path.name}, l.{line_number}: expected 5 columns")
                    ps_payment_method, with_vat, client_code, currency, territoriality, ebp_payment_method = rows
                    with_vat = with_vat == 'AVEC'
                    self.payment_method_mapping.setdefault(ps_payment_method.strip(), {})
                    self.payment_method_mapping[ps_payment_method.strip()][with_vat] = (
                        client_code.strip(),
                        currency.strip(),
                        territoriality.strip(),
                        ebp_payment_method.strip())

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
                    vat = float(vat.replace(',','.')) / 100

                    self.vat_mapping[territoriality][ps_country_id] = (vat, ebp_id)
                line_number += 1

    def run(self) -> int:
        try:
            self.load_payment_method_mapping()
            self.logger.debug(f"payment method mapping: {self.payment_method_mapping}")
            self.load_vat_mapping()
            self.logger.debug(f"vat mapping: {self.vat_mapping}")
            self.check_consistency()
            assert self.webservice.test_api_authentication(), "Unable to login"
            if self.mailer:
                self.mailer.try_login()
            self.countries_iso_code = self.webservice.get_countries_iso_code()
            self.logger.debug(f"countries iso codes: {self.countries_iso_code}")
            self.currencies_iso_code = self.webservice.get_currencies_iso_code()
            self.logger.debug(f"currencies iso codes: {self.currencies_iso_code}")
            self.logger.info("Starting orders retrieving")
            self.export_orders_and_products()
            self.import_files()
            self.logger.handlers[2].flush()
            self.logger.handlers[2].close()
            self.logger.debug(f"errors_logged: {self.errors_logged}")
            self.logger.debug(f"errors_raised_by_ebp: {self.errors_raised_by_ebp}")
            if self.mailer and (self.errors_logged or self.errors_raised_by_ebp):
                self.mailer.send_mail("PS EBP Connector - Erreurs lors de l'exécution",
                                      "Des erreurs ont été constatées lors de l'exécution du connecteur, consultez les "
                                      "journaux en PJ.",
                                      "contact@guillaumechinal.fr",
                                      [self._logs_file_path, self._ebp_import_products_logs_path, self._ebp_import_orders_logs_path])

            return 0
        except Exception as e:
            self.logger.critical("A critical error was raised, see below")
            self.logger.exception(e)
            return 1
