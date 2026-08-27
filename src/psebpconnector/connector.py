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
import re
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
    # Delai max d'un import EBP (s). Sans timeout, un EBP fige bloque le connecteur indefiniment.
    _EBP_TIMEOUT = 1800

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
        self.pending_orders = []
        # None tant qu'EBP n'a pas rendu la main (timeout, lancement impossible) -> pas de marquage.
        self.ebp_products_returncode = None
        self.ebp_orders_returncode = None
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
        country_id = int(country_id)
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
        ps_country_id = int(ps_country_id)
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
        delivery_address = self._get_order_delivery_address(order)
        vat_applied = False if delivery_address.id_country == 21 else self._check_if_vat_applied(order)
        ebp_client_code, currency, territoriality, ebp_payment_method = self._get_info_from_payment_method(order, vat_applied)
        invoice_address = self._get_order_invoice_address(order)
        vat_value, ebp_vat_id = self._get_order_vat(order, territoriality, delivery_address.id_country, vat_applied)
        order_rows = self._get_order_rows(order)
        # ECRITURE ATOMIQUE : on construit TOUTES les lignes du document en memoire d'abord.
        # Si une seule ligne echoue (produit 404, 429 epuise, montant illisible...), on sort par
        # exception SANS avoir rien ecrit : le CSV ne contient jamais un document amputé qu'EBP
        # importerait comme une facture incomplete (et qui serait recreee a chaque run puisque la
        # commande ne serait pas dans pending_orders).
        buffered_products = []
        buffered_rows = []
        buffered_product_ids = set()
        for order_row in order_rows:
            product = self.export_product(order_row.product_id, already_buffered=buffered_product_ids)
            if product is not None:
                buffered_products.append(product)
                buffered_product_ids.add(order_row.product_id)
            buffered_rows.append(
                self.export_order_row(order, order_row, delivery_address, invoice_address, ebp_vat_id,
                                      ebp_client_code, ebp_payment_method, territoriality, vat_value))

        # A partir d'ici plus rien ne peut echouer : on materialise le document complet.
        for product in buffered_products:
            self._write_csv_line(product, self.csv_products)
        self.exported_products.update(buffered_product_ids)
        for export_order_row in buffered_rows:
            self._write_csv_line(export_order_row, self.csv_orders)

        # Ne PAS marquer exported ici : on attend la confirmation de l'import EBP
        # (cf. mark_exported_orders) pour ne pas perdre une commande rejetee par EBP.
        self.pending_orders.append(order)

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

    # Compteur d'enregistrements EBP : "12/12 enregistrements ont ete importes".
    # On ancre sur le mot "enregistrement" pour ne PAS confondre avec une date (26/08/2026)
    # presente dans un message d'erreur (base verrouillee, etc.).
    _EBP_RECORDS_RE = re.compile(r'(\d+)\s*/\s*(\d+)\s+enregistrement', re.IGNORECASE)

    @classmethod
    def _parse_ebp_imported_records(cls, log: str):
        """ Retourne (importes, total) d'apres le compteur EBP, ou None si absent du log. """
        result = cls._EBP_RECORDS_RE.search(log)
        if not result:
            return None
        return int(result.group(1)), int(result.group(2))

    @staticmethod
    def check_ebp_records_imported(log: str) -> bool:
        result = re.search(r'(\d+)/(\d+)', log)

        # Let's say empty log is okay
        if not result:
            return True

        return int(result.group(1)) == int(result.group(2))

    def errors_logged(self):
        return self.logger.handlers[3].log_emitted

    def errors_raised_by_ebp(self):
        if not self._ebp_import_orders_logs_path.is_file() or not self._ebp_import_products_logs_path.is_file():
            return True
        orders_log = self._ebp_import_orders_logs_path.read_text().lower()
        products_log = self._ebp_import_products_logs_path.read_text().lower()
        # EBP a explicitement signale une erreur (base verrouillee par un autre utilisateur, base non
        # ouverte, document rejete...) : dans ce cas il n'y a parfois AUCUN compteur d'enregistrements
        # dans le log, il faut donc alerter sur le marqueur d'erreur lui-meme.
        if '--erreur--' in orders_log or '--erreur--' in products_log:
            return True
        return not (self.check_ebp_records_imported(orders_log) and
                self.check_ebp_records_imported(products_log))

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
            document_client_name=f"{invoice_address.lastname.upper().replace(';', '')} {invoice_address.firstname.upper().replace(';', '')}",
            document_invoice_address_1=f"{invoice_address.address1.replace(';', '')}",
            document_invoice_address_2=f"{invoice_address.address2.replace(';', '')}",
            document_invoice_address_3='',
            document_invoice_address_4='',
            document_invoice_zip_code=f"{invoice_address.postcode.replace(';', '')}",
            document_invoice_city=f"{invoice_address.city.replace(';', '')}",
            document_invoice_department='',
            document_invoice_country_iso_code=self._get_country_iso_code(invoice_address.id_country),
            document_invoice_lastname=f"{invoice_address.lastname.upper().replace(';', '')}",
            document_invoice_firstname=f"{invoice_address.firstname.upper().replace(';', '')}",
            document_invoice_phone=f"{invoice_address.phone}",
            document_invoice_mobile_phone=f"{invoice_address.phone_mobile}",
            document_invoice_fax='',
            document_invoice_email='nomail@nomail.fr',
            document_delivery_address_1=f"{delivery_address.address1.replace(';', '')}",
            document_delivery_address_2=f"{delivery_address.address2.replace(';', '')}",
            document_delivery_address_3='',
            document_delivery_address_4='',
            document_delivery_zip_code=f"{delivery_address.postcode}",
            document_delivery_city=f"{delivery_address.city.replace(';', '')}",
            document_delivery_department='',
            document_delivery_country_iso_code=self._get_country_iso_code(delivery_address.id_country),
            document_delivery_lastname=f"{delivery_address.lastname.upper().replace(';', '')}",
            document_delivery_firstname=f"{delivery_address.firstname.upper().replace(';', '')}",
            document_delivery_phone=f"{delivery_address.phone}",
            document_delivery_mobile_phone=f"{delivery_address.phone_mobile}",
            document_delivery_fax='',
            document_delivery_email='nomail@nomail.fr',
            document_territoriality=ebp_territoriality,
            document_vat_number="" if str(invoice_address.vat_number) == '0' else str(invoice_address.vat_number).replace(' ', '').upper(),
            document_discount_pct=f"{round(float(order.total_discounts) / float(order.total_products_wt) * 100, 6):06f}" if float(order.total_products_wt) else '0.000000',
            document_discount_amount=f"{order.total_discounts}",
            document_escompte_pct='',
            document_escompte_amount='',
            document_shipping_cost_code='',
            document_shipping_cost_notax=f"{round((float(order.total_shipping) / (1 + vat_rate)), 6):06f}",
            document_shipping_cost_vat_rate=f"{round(vat_rate * 100, 6)}",
            document_shipping_tva_code=f"{ebp_vat_id}",
            document_total_notax='',
            document_total='' if float(order.total_discounts) > 0 else f"{round((float(order.total_products_wt) + float(order.total_shipping)), 6):06f}",
            document_notes=f"Commande importée n°{order.id} - {order.reference}",
            line_product_code=f"{order_row.product_ean13}",
            line_description=f"{order_row.product_name}",
            line_quantity=f"{order_row.product_quantity}",
            line_vat_rate=f"{round(vat_rate * 100, 6):06f}",
            line_vat_code=f"{ebp_vat_id}",
            document_commercial_code='',
            line_unit_price_notax='',
            line_unit_price=f"{round(float(order_row.unit_price_tax_incl), 6):06f}",
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
            # Meme garde que document_total : en presence d'une remise, on laisse EBP recalculer le
            # montant en devise, sinon la facture/l'avoir sort au montant AVANT remise.
            document_currency_amount='' if float(order.total_discounts) > 0 else (f"{round(float(order.total_products_wt) + float(order.total_shipping), 6):06f}" if float(order.conversion_rate) != 1.0 else ''),
            document_currency_amount_notax='',
            document_currency_amount_shipping_notax=f"{round(float(order.total_shipping) / (1 + vat_rate), 6):06f}" if float(order.conversion_rate) != 1.0 else '',
            line_currency_unit_price_notax=f"{round(float(order_row.product_price), 6):06f}" if float(order.conversion_rate) != 1.0 else '',
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
            if export_order_row.document_total:
                export_order_row.document_total = f"-{export_order_row.document_total}"
            export_order_row.line_quantity = f"-{export_order_row.line_quantity}"
            export_order_row.document_shipping_cost_notax = f"-{export_order_row.document_shipping_cost_notax}"
            if export_order_row.document_currency_amount:
                export_order_row.document_currency_amount = f"-{export_order_row.document_currency_amount}"
            if export_order_row.document_currency_amount_shipping_notax:
                export_order_row.document_currency_amount_shipping_notax = f"-{export_order_row.document_currency_amount_shipping_notax}"
            export_order_row.document_number_suffix += "11"
            export_order_row.document_number += "11"
        self.logger.debug(f"Order {order.id}, export_order_row: {export_order_row}")
        # NE PAS ecrire ici : c'est _process_order qui materialise le document une fois complet
        # (ecriture atomique, cf. _process_order).
        return export_order_row

    def export_product(self, product_id: int, already_buffered=frozenset()):
        """ Construit la fiche article a importer, ou None si elle a deja ete emise.
            L'ecriture (et l'ajout a self.exported_products) est faite par _process_order une fois
            la commande entierement construite : un echec en cours de commande ne doit pas laisser
            croire que l'article a ete exporte. """
        if product_id in self.exported_products or product_id in already_buffered:
            return None
        self.logger.info(f"Exporting product {product_id}")
        product = self.webservice.get_product(product_id)
        product_name = product.name
        if isinstance(product_name, list):
            product_name = product.name[0]['value']
        export_product = ExportProduct(
            code=product.ean13,
            name=product_name,
            type='BIEN',
            price=f"{float(product.price):06f}",
            wholesale_price=f"{float(product.wholesale_price):06f}",
            ean=product.ean13)
        self.logger.debug(f"{export_product}")
        return export_product

    def _iter_orders_to_export(self):
        """ Enveloppe le generateur du webservice : une exception pendant la pagination interrompt
            proprement la recuperation (les commandes deja recuperees sont conservees et importees)
            au lieu de faire remonter l'erreur et d'avorter tout le run. """
        # iter() : le webservice renvoie un generateur en production, mais les tests peuvent
        # fournir une simple liste.
        generator = iter(self.webservice.get_orders_to_export(self.config.order_valid_status,
                                                              self.config.order_refund_status))
        while True:
            try:
                order = next(generator)
            except StopIteration:
                return
            except Exception as e:
                self.logger.error(f"Recuperation des commandes interrompue ({e}) : le run continue avec les "
                                  f"commandes deja recuperees.")
                return
            yield order

    def export_orders_and_products(self):
        exported_orders_counter = 0
        seen = set()
        # Le try/except de la boucle n'attrape PAS une exception levee par le generateur lui-meme
        # (pagination, get_order...). Sans ce garde, un 404/JSON invalide en cours de pagination
        # avorterait le run ET empecherait l'import des commandes deja construites.
        orders = self._iter_orders_to_export()
        for order in orders:
            key = (order.id, order.is_refund)
            if key in seen:
                self.logger.warning(f"Order {order.id}: deja traitee dans ce run, ignoree (anti-doublon)")
                continue
            seen.add(key)
            if self.config.order_limit and exported_orders_counter >= self.config.order_limit:
                break
            try:
                self._process_order(order)
            except InvalidOrder:
                self.logger.warning(f"Skipping order {order.id}")
                if order.is_refund:
                    self.webservice.refund_error_counter += 1
                else:
                    self.webservice.order_error_counter += 1
            except Exception as e:
                # Filet: une exception inattendue sur UNE commande ne doit JAMAIS tuer tout
                # le run (sinon plus aucune commande importee). On logge, on skippe, on continue.
                self.logger.error(f"Order {order.id}: erreur inattendue, commande ignoree (le run continue) - {e}")
                if order.is_refund:
                    self.webservice.refund_error_counter += 1
                else:
                    self.webservice.order_error_counter += 1
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
        self.ebp_products_returncode = self._run_ebp(import_products_command, 'articles')

        self.logger.info('Importing orders')
        self.logger.debug(f"Subprocess args: {import_orders_command}")
        self.ebp_orders_returncode = self._run_ebp(import_orders_command, 'commandes')

    def _run_ebp(self, command, label):
        """ Lance EBP avec un timeout : sans lui, un EBP fige (boite de dialogue, base occupee)
            bloque le connecteur indefiniment et les runs horaires s'empilent.
            Retourne le code retour, ou None si EBP n'a pas rendu la main / n'a pas pu demarrer. """
        try:
            result = subprocess.run(command, timeout=self._EBP_TIMEOUT)
        except subprocess.TimeoutExpired:
            self.logger.error(f"Import EBP ({label}) : delai de {self._EBP_TIMEOUT}s depasse, processus interrompu. "
                              f"Aucune commande ne sera marquee exportee (rejeu au prochain run).")
            return None
        except OSError as e:
            self.logger.error(f"Import EBP ({label}) : impossible de lancer EBP - {e}")
            return None
        if result.returncode != 0:
            self.logger.error(f"Import EBP ({label}) : EBP a retourne le code {result.returncode}")
        return result.returncode

    def mark_exported_orders(self):
        """ Marque les commandes comme exportees dans PrestaShop UNIQUEMENT pour les documents
            reellement importes par EBP. Les commandes rejetees par EBP (ou si le log d'import est
            absent/illisible) sont laissees a exported=0 pour etre rejouees au prochain run plutot
            que perdues silencieusement. """
        if self.ebp_orders_returncode is None:
            self.logger.error("Import EBP interrompu (delai depasse ou EBP n'a pas pu demarrer) : aucune commande "
                              "marquee exportee (rejeu au prochain run)")
            return
        if not self._ebp_import_orders_logs_path.is_file():
            self.logger.error("Log d'import EBP absent : aucune commande marquee exportee (rejeu au prochain run)")
            return
        log = self._ebp_import_orders_logs_path.read_text(encoding='utf-8', errors='ignore')
        # ATTENTION : ne PAS chercher un simple r'\d+/\d+' ici, une DATE dans un message d'erreur
        # (ex. "verrouillee ... par ADM depuis le 26/08/2026") matcherait et ferait croire a un
        # import reussi -> toutes les commandes marquees exportees SANS facture EBP.
        # On exige le vrai compteur d'enregistrements EBP.
        has_error_marker = '--erreur--' in log.lower()
        imported = self._parse_ebp_imported_records(log)
        if imported is None:
            # Pas de compteur exploitable. On NE retombe PAS sur un r'\d+/\d+' brut : une date
            # ("26/08/2026") passerait pour un ratio d'import et ferait marquer des commandes non
            # facturees (regression du 26/08). On se fie au code retour d'EBP, qui est fiable :
            # 0 = import realise (libelle du log different, log tronque...), sinon echec.
            if not has_error_marker and self.ebp_orders_returncode == 0:
                self.logger.warning("Log d'import EBP sans compteur d'enregistrements mais EBP a retourne 0 : "
                                    "import considere comme reussi (marquage effectue).")
                imported = None  # pas de compteur : on marque tout ce qui n'est pas explicitement rejete
            else:
                self.logger.error("Import EBP non confirme (base verrouillee, EBP non demarre, delai depasse ou code "
                                  "retour non nul) : aucune commande marquee exportee (rejeu au prochain run)")
                return
        else:
            done, total = imported
            if done == 0:
                self.logger.error(f"Import EBP totalement en echec ({done}/{total}) : aucune commande marquee exportee "
                                  f"(rejeu au prochain run)")
                return
        rejected = set(re.findall(r'Le document (\d+) ne sera pas import', log))
        for order in self.pending_orders:
            document_number = f"{order.id}11" if order.is_refund else f"{order.id}"
            if document_number in rejected:
                self.logger.warning(f"Order {order.id}: rejetee par EBP (document {document_number}), "
                                    f"laissee a exported=0 pour rejeu")
                continue
            # Une erreur HTTP sur UNE commande ne doit pas interrompre le marquage des suivantes :
            # elles sont deja facturees dans EBP, les laisser a exported=0 les ferait re-importer
            # au run suivant => doublons de factures.
            try:
                if order.is_refund:
                    self.webservice.set_order_refund(order)
                else:
                    self.webservice.set_order_exported(order)
            except Exception as e:
                self.logger.error(f"Order {order.id}: FACTUREE dans EBP mais le marquage PrestaShop a echoue ({e}). "
                                  f"ATTENTION : risque de doublon au prochain run, verifier manuellement.")

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

                    self.vat_mapping[territoriality][int(ps_country_id)] = (vat, ebp_id)
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
                # L'alerte mail est un sous-systeme secondaire : son indisponibilite ne doit pas
                # empecher la facturation. On logge et on continue sans mailer.
                try:
                    self.mailer.try_login()
                except Exception as e:
                    self.logger.error(f"Connexion O365 impossible, les alertes mail sont desactivees pour ce run - {e}")
                    self.mailer = None
            self.countries_iso_code = self.webservice.get_countries_iso_code()
            self.logger.debug(f"countries iso codes: {self.countries_iso_code}")
            self.currencies_iso_code = self.webservice.get_currencies_iso_code()
            self.logger.debug(f"currencies iso codes: {self.currencies_iso_code}")
            self.logger.info("Starting orders retrieving")
            self.export_orders_and_products()
            self.import_files()
            self.mark_exported_orders()
            self.logger.handlers[2].flush()
            self.logger.handlers[2].close()
            self.logger.debug(f"errors_logged: {self.errors_logged()}")
            self.logger.debug(f"errors_raised_by_ebp: {self.errors_raised_by_ebp()}")
            return 0
        except Exception as e:
            self.logger.critical("A critical error was raised, see below")
            self.logger.exception(e)
            return 1

        finally:
            if self.mailer and (self.errors_logged() or self.errors_raised_by_ebp()):
                self.mailer.send_mail("PS EBP Connector - Erreurs lors de l'exécution",
                                      "Des erreurs ont été constatées lors de l'exécution du connecteur, consultez les "
                                      "journaux en PJ.",
                                      self.config.o365_recipient,
                                      [
                                          f for f in [
                                            self._logs_file_path,
                                            self._ebp_import_products_logs_path,
                                            self._ebp_import_orders_logs_path,
                                            self._csv_products_path,
                                            self._csv_orders_path
                                          ]
                                          if f.is_file()
                                      ])
