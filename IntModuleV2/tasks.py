import json

from celery import shared_task
from Main.models import PriceChecker, QuantityChecker
from Main.helpers import RetailCRMHelper

from Main.views import try_zone_login, get_access_token, zone_get_product_quantity, \
    zone_update_quantity, zone_get_product_price, zone_update_price


@shared_task(name='update_products_price')
def update_products_price(retail_address, retail_api_key, access_token, refresh_token, products):
    acc_token = access_token
    retail_helper = RetailCRMHelper()
    retail_helper.init_and_setup(retail_address, retail_api_key)
    access_token_check = try_zone_login(acc_token)
    json_products = json.loads(products)
    if not access_token_check:
        refresh_token_check, acc_token = get_access_token(refresh_token)
        if not refresh_token_check:
            PriceChecker.objects.get(retail_address=retail_address,
                                     retail_api_key=retail_api_key,
                                     products=products).delete()

    for product in json_products:
        retail_price = retail_helper.get_offer_price(product['retail_id'])
        zone_price = zone_get_product_price(acc_token,
                                            product['zone_listing_id'],
                                            product['zone_product_id'])
        if retail_price != zone_price:
            if zone_update_price(acc_token,
                                 product['zone_product_id'],
                                 product['zone_listing_id'],
                                 retail_price):
                print("Successfully updated price")
            else:
                print("Price wasn't updated")


@shared_task(name='update_products_quantity')
def update_products_quantity(retail_address, retail_api_key, access_token, refresh_token, products):
    acc_token = access_token
    retail_helper = RetailCRMHelper()
    retail_helper.init_and_setup(retail_address, retail_api_key)
    access_token_check = try_zone_login(acc_token)
    json_products = json.loads(products)
    if not access_token_check:
        refresh_token_check, acc_token = get_access_token(refresh_token)
        if not refresh_token_check:
            QuantityChecker.objects.get(retail_address=retail_address,
                                        retail_api_key=retail_api_key,
                                        products=products).delete()

    for product in json_products:
        product_id = list()
        product_id.append(product['retail_id'])
        retail_check, retail_quantity = retail_helper.get_product_quantity(product_id)
        if not retail_check:
            continue
        zone_quantity = zone_get_product_quantity(acc_token,
                                                  product['zone_listing_id'],
                                                  product['zone_product_id'],
                                                  product['warehouse_id'])
        if retail_quantity != zone_quantity:
            if zone_update_quantity(acc_token, product['zone_product_id'], product['warehouse_id'], retail_quantity):
                print("Successfully updated quantity")
            else:
                print("Quantity wasn't updated")



