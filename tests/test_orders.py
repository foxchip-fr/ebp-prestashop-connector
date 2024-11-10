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

import json

from pathlib import Path
from psebpconnector.connector import Connector
from psebpconnector.models import *

ORDER_1 = Order.from_dict(json.loads('{"order":{"id":549085,"id_address_delivery":967452,"id_address_invoice":967452,"id_cart":817776,"id_currency":1,"id_lang":1,"id_customer":532822,"id_carrier":103,"current_state":4,"module":"feedbiz","invoice_number":541557,"invoice_date":"2024-07-05 19:40:27","delivery_number":528463,"delivery_date":"2024-07-08 10:52:56","valid":"1","date_add":"2024-07-05 16:40:18","date_upd":"2024-10-23 11:09:16","shipping_number":"885000009059824","id_shop_group":1,"id_shop":1,"secure_key":"f6e7751671880b23ba68281089d71d35","payment":"Amazon - FR","total_discounts":"0.000000","total_discounts_tax_incl":"0.000000","total_discounts_tax_excl":"0.000000","total_paid":"20.230000","total_paid_tax_incl":"20.230000","total_paid_tax_excl":"16.860000","total_paid_real":"40.460000","total_products":"9.780000","total_products_wt":"11.730000","total_shipping":"8.500000","total_shipping_tax_incl":"8.500000","total_shipping_tax_excl":"7.080000","carrier_tax_rate":"20.000","total_wrapping":"0.000000","total_wrapping_tax_incl":"0.000000","total_wrapping_tax_excl":"0.000000","round_mode":2,"round_type":2,"conversion_rate":"1.000000","reference":"FMHGOYBGK","associations":{"order_rows":[{"id":983222,"product_id":52695,"product_attribute_id":0,"product_quantity":1,"product_name":"Porte Clé Capitaine Flam - Professeur Simon Gomme 8cm","product_reference":"4589504961513","product_ean13":"4589504961513","product_isbn":"","product_upc":"","product_price":"9.775000","id_customization":0,"unit_price_tax_incl":"11.730000","unit_price_tax_excl":"9.775000"}]}}}')['order'])
PRODUCT_1 = Product.from_dict(json.loads('{"product":{"id":59989,"id_manufacturer":538,"id_supplier":11,"id_category_default":30106305,"id_default_image":132903,"id_tax_rules_group":102,"position_in_category":51,"manufacturer_name":"Bandai Hobby","type":"simple","id_shop_default":1,"reference":"4573102616029","width":"0.000000","height":"0.000000","depth":"0.000000","weight":"1.500000","ean13":"4573102616029","state":1,"additional_delivery_times":1,"delivery_in_stock":[{"id":1,"value":null},{"id":2,"value":null}],"delivery_out_stock":[{"id":1,"value":null},{"id":2,"value":null}],"ecotax":"0.000000","minimal_quantity":1,"price":"24.166667","wholesale_price":"15.255000","unit_price":"0.000000","unit_price_ratio":"0.000000","additional_shipping_cost":"0.000000","active":"1","redirect_type":"404","available_for_order":"1","available_date":"2024-11-09","condition":"new","show_price":"1","indexed":"1","visibility":"both","date_add":"2021-02-27 11:18:25","date_upd":"2024-07-05 19:01:01","pack_stock_type":3,"meta_description":[{"id":1,"value":"- Maquette Gundam - 017 Wing Gundam Zero Endless Waltz Gunpla RG 1\/144- Armure Gundam  pour le modèle Nepteight articulée à assembler- Système de montage SNA..."},{"id":2,"value":"- Maquette Gundam - 017 Wing Gundam Zero Endless Waltz Gunpla RG 1\/144- Armure Gundam  pour le modèle Nepteight articulée à assembler- Système de montage SNA..."}],"meta_keywords":[{"id":1,"value":"4573102616029,Maquette Gundam - 017 Wing Gundam Zero Endless Waltz Gunpla RG 1\/144 13cm,RG,Bandai Hobby"},{"id":2,"value":"4573102616029,Maquette Gundam - 017 Wing Gundam Zero Endless Waltz Gunpla RG 1\/144 13cm,RG,Bandai Hobby"}],"meta_title":[{"id":1,"value":"Maquette Gundam - 017 Wing Gundam Zero Endless Waltz Gunpla RG 1\/14..."},{"id":2,"value":"Maquette Gundam - 017 Wing Gundam Zero Endless Waltz Gunpla RG 1\/14..."}],"link_rewrite":[{"id":1,"value":"maquette-gundam-017-wing-gundam-zero-endless-waltz-gunpla-rg-1-144-13cmrg"},{"id":2,"value":"maquette-gundam-017-wing-gundam-zero-endless-waltz-gunpla-rg-1-144-13cmrg"}],"name":[{"id":1,"value":"Maquette Gundam - 017 Wing Gundam Zero Endless Waltz Gunpla RG 1\/144 13cm"},{"id":2,"value":"Maquette Gundam - 017 Wing Gundam Zero Endless Waltz Gunpla RG 1\/144 13cm"}],"description":[{"id":1,"value":"<p>- Maquette Gundam - <span>017 Wing Gundam Zero Endless Waltz<\/span> Gunpla RG 1\/144<br \/><span>- Armure<span> Gundam  pour le modèle Nepteight articulée à assembler<\/span><br \/><\/span>- <span>Système de montage <\/span><em>SNAPFIT<\/em><span> = ne nécessite ni colle, ni peinture<\/span><br \/>- Vendu sous boite carton<br \/>- Taille 13cm<\/p>"},{"id":2,"value":"<p>- Maquette Gundam - <span>017 Wing Gundam Zero Endless Waltz<\/span> Gunpla RG 1\/144<br \/><span>- Armure<span> Gundam  pour le modèle Nepteight articulée à assembler<\/span><br \/><\/span>- <span>Système de montage <\/span><em>SNAPFIT<\/em><span> = ne nécessite ni colle, ni peinture<\/span><br \/>- Vendu sous boite carton<br \/>- Taille 13cm<\/p>"}],"description_short":[{"id":1,"value":""},{"id":2,"value":""}],"available_now":[{"id":1,"value":"En Stock"},{"id":2,"value":"Available"}],"available_later":[{"id":1,"value":"Rupture"},{"id":2,"value":"Out of Stock"}],"associations":{"categories":[{"id":30106305}],"images":[{"id":132903}],"tags":[{"id":57},{"id":105},{"id":106},{"id":107},{"id":700},{"id":701},{"id":737},{"id":739},{"id":771}],"stock_availables":[{"id":60251,"id_product_attribute":0}]}}}')['product'])
ADDRESS_1 = Address(id=967452, id_country=8)

def test_order(mocker):
    mocker.patch('psebpconnector.webservice.Webservice.get_orders_to_export', return_value=[ORDER_1])
    mocker.patch('psebpconnector.webservice.Webservice.get_address', return_value=ADDRESS_1)
    mocker.patch('psebpconnector.webservice.Webservice.get_product', return_value=PRODUCT_1)
    connector = Connector(Path(__file__).parent / 'samples/config/config_file_ok.ini')
    connector.load_payment_method_mapping()
    connector.load_vat_mapping()
    connector.export_orders_and_products()

