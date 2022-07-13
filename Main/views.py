import datetime
import json

import requests
from django.shortcuts import render
from django.views import View

from IntModuleV2.enums import TimeInterval

from Main.forms import ZoneSmartLoginForm, ExportProductsForm
from Login.views import auth_helper
from Main.models import PriceChecker, QuantityChecker
from Main.helpers import RetailCRMHelper
from django.utils.translation import gettext_lazy as _


def get_access_token(refresh_token: str):
    header = {
        'Content-Type': 'application/json',
    }
    data = {
        "refresh": refresh_token
    }
    response = requests.post("https://api.zonesmart.com/v1/auth/jwt/refresh/", headers=header, json=data)
    converted_response = json.loads(response.text)
    if response.status_code == 200:
        access_token = converted_response['access']
        return True, access_token
    else:
        return False, ""


def check_zone_cookies(request):
    try:  # Пробуем получить адрес и ключ апи из кукисов
        email = request.session['zone_email']
        password = request.session['zone_pass']
        refresh_token = request.session['refresh_token']
        access_token = request.session['access_token']
    except:  # Если что-то идёт не так, то делаем их None
        email = None
        password = None
        refresh_token = None
        access_token = None
    if email is None or password is None or refresh_token is None or access_token is None:
        return False, "", "", "", ""
    else:
        return True, email, password, refresh_token, access_token


def check_retail_cookies(request):
    try:  # Пробуем получить адрес и ключ апи из кукисов
        address = request.session['address']
        api_key = request.session['api_key']
    except:  # Если что-то идёт не так, то делаем их None
        address = None
        api_key = None
    if address is None or api_key is None:
        return False, "", ""
    else:
        return True, address, api_key


def try_zone_login(access_token: str):
    header = {
        'Content-Type': 'application/json',
        'Authorization': 'JWT ' + access_token
    }
    r = requests.get("https://api.zonesmart.com/v1/zonesmart/marketplace/", headers=header)
    if r.status_code == 200:
        return True
    else:
        return False


def init_retail_helper(request):
    address = request.session['address']
    api_key = request.session['api_key']
    retail_helper = RetailCRMHelper()
    retail_helper.init_and_setup(address, api_key)
    return retail_helper


class ExportedProduct:
    def __init__(self, retail_id, zone_listing_id, zone_product_id, warehouse_id):
        self.retail_id = retail_id
        self.zone_listing_id = zone_listing_id
        self.zone_product_id = zone_product_id
        self.warehouse_id = warehouse_id

    def to_dict(self):
        return {'retail_id': self.retail_id,
                'zone_listing_id': self.zone_listing_id,
                'zone_product_id': self.zone_product_id,
                'warehouse_id': self.warehouse_id}


def zone_create_listings(listings, access_token, warehouse_id):
    header = {
        'Content-Type': 'application/json',
        'Authorization': 'JWT ' + access_token
    }
    results = dict()
    results2 = list()
    for listing in listings:
        json_product = listing.to_json()
        correct_json = json.loads(json_product)
        response = requests.post("https://api.zonesmart.com/v1/zonesmart/listing/", headers=header,
                                 json=correct_json)
        if response.status_code == 201:
            created_listing = json.loads(response.text)
            created_listing_products = created_listing['products']
            for product in created_listing_products:
                results2.append(ExportedProduct(product['sku'],
                                                created_listing['id'],
                                                product['id'],
                                                warehouse_id))
        results[listing.title] = response.status_code
    return results, results2


def zone_warehouse_set_default(access_token, warehouse_id):
    header = {
        'Content-Type': 'application/json',
        'Authorization': 'JWT ' + access_token
    }
    response = requests.post(f"https://api.zonesmart.com/v1/zonesmart/warehouse/{warehouse_id}/set_default/",
                             headers=header)
    if response.status_code == 200:
        return True
    else:
        return False


def zone_get_product_quantity(access_token, listing_id, product_id, warehouse_id):
    header = {
        'Content-Type': 'application/json',
        'Authorization': 'JWT ' + access_token
    }
    response = requests.get(f"https://api.zonesmart.com/v1/zonesmart/listing/{listing_id}/product/{product_id}/",
                            headers=header)
    listing = json.loads(response.text)
    products_inventories = listing['product_inventories']
    for product in products_inventories:
        temp_warehouse_id = product['warehouse']
        if warehouse_id == temp_warehouse_id:
            return product['quantity']


def zone_get_product_price(access_token, listing_id, product_id):
    header = {
        'Content-Type': 'application/json',
        'Authorization': 'JWT ' + access_token
    }
    response = requests.get(f"https://api.zonesmart.com/v1/zonesmart/listing/{listing_id}/product/{product_id}/",
                            headers=header)
    listing = json.loads(response.text)
    price = listing['price']
    return price


def zone_update_price(access_token, product_id, listing_id, quantity):
    header = {
        'Content-Type': 'application/json',
        'Authorization': 'JWT ' + access_token
    }
    data = {
        'price': quantity
    }
    response = requests.patch(f"https://api.zonesmart.com/v1/zonesmart/listing/{listing_id}/product/{product_id}/",
                              headers=header,
                              json=data)
    if response.status_code == 200:
        return True
    else:
        return False


def zone_update_quantity(access_token, product_id, warehouse_id, quantity):
    header = {
        'Content-Type': 'application/json',
        'Authorization': 'JWT ' + access_token
    }
    data = {
        'inventory': [{
            'product': product_id,
            'warehouse': warehouse_id,
            'quantity': quantity
        }]
    }
    response = requests.post("https://api.zonesmart.com/v1/zonesmart/product_inventory/bulk_update/", headers=header,
                             json=data)
    if response.status_code == 200:
        return True
    else:
        return False


def zone_create_warehouse(access_token):
    header = {
        'Content-Type': 'application/json',
        'Authorization': 'JWT ' + access_token
    }
    data = {
        'name': 'Export from RetailCRM at: ' + datetime.datetime.now().__str__()
    }
    response = requests.post("https://api.zonesmart.com/v1/zonesmart/warehouse/", headers=header, json=data)
    warehouse_id = json.loads(response.text)['id']
    return warehouse_id


class ExportProductsView(View):
    template_name = 'main_export_products.html'
    http_method_names = ['get', 'post']

    def post(self, request):
        retail_helper = init_retail_helper(request)
        choices, groups_dict = retail_helper.get_product_groups()
        form = ExportProductsForm(choices)

        active = request.POST.get('active')
        min_quantity = request.POST.get('min_quantity')
        groups = request.POST.getlist('groups')
        quantity_period = request.POST.get('quantity_check_period')
        price_sync = request.POST.get('price_sync')

        access_token = request.session['access_token']
        refresh_token = request.session['refresh_token']
        # products list
        products_to_export = retail_helper.get_products(access_token, groups_dict, active, min_quantity, groups)
        # need to create warehouse to exported products
        warehouse_id = zone_create_warehouse(access_token)
        zone_warehouse_set_default(access_token, warehouse_id)
        # export_results - array with all products and their status codes
        export_results, exported_products_creds = zone_create_listings(products_to_export, access_token, warehouse_id)

        # Need to convert list of objects to json because celery cant understand complex python objects
        temp_exported_products_creds = [obj.to_dict() for obj in exported_products_creds]
        json_exported_products_creds = json.dumps(temp_exported_products_creds)

        QuantityChecker.objects.create(retail_address=retail_helper.address,
                                       retail_api_key=retail_helper.api_key,
                                       access_token=access_token,
                                       refresh_token=refresh_token,
                                       period=TimeInterval[quantity_period],
                                       products=json_exported_products_creds)
        if price_sync == '1':
            price_sync_period = request.POST.get('price_check_period')
            PriceChecker.objects.create(retail_address=retail_helper.address,
                                        retail_api_key=retail_helper.api_key,
                                        access_token=access_token,
                                        refresh_token=refresh_token,
                                        period=TimeInterval[price_sync_period],
                                        products=json_exported_products_creds)

        # count - variable with number of succesf. exported products
        count = sum(value == 201 for value in export_results.values())
        if count != 0:
            return render(request, self.template_name,
                          context={"form": form,
                                   "zone_status": True,
                                   "modal_show": True,
                                   "modal_text": _('Successfully transferred %(count)s products') % {'count': count}})
        else:
            return render(request, self.template_name,
                          context={"form": form,
                                   "zone_status": True,
                                   "modal_show": True,
                                   "modal_text": _("There was some kind of error while exporting")})

    def get(self, request):
        retail_helper = init_retail_helper(request)
        choices, groups_dict = retail_helper.get_product_groups()
        # print(choices)
        form = ExportProductsForm(choices)
        return render(request, self.template_name,
                      context={'zone_status': try_zone_login(request.session['access_token']),
                               'form': form})


class ZoneAccountView(View):
    template_name = 'main_zone_acc.html'
    http_method_names = ['get', 'post']

    def post(self, request):
        form = ZoneSmartLoginForm(request.POST)
        email = request.POST.get("email")
        password = request.POST.get("password")
        zone_login_check, access_token, refresh_token = auth_helper.create_zone_tokens(email, password)

        if zone_login_check:
            request.session['zone_email'] = email
            request.session['zone_pass'] = password
            request.session['access_token'] = access_token
            request.session['refresh_token'] = refresh_token
            return render(request, self.template_name, context={"form": form,
                                                                "auth_state": zone_login_check,
                                                                "zone_status": zone_login_check})
        else:
            return render(request, self.template_name, context={"form": form,
                                                                "auth_state": zone_login_check})

    def get(self, request):

        zone_cookie_check, email, password, refresh_token, access_token = check_zone_cookies(request)
        # QuantityChecker.objects.create(retail_email=request.session['address'])
        form = ZoneSmartLoginForm(initial={'email': email,
                                           'password': password}, auto_id=False)
        match zone_cookie_check:
            case True:
                access_token_check = try_zone_login(access_token)
                if access_token_check:
                    return render(request, self.template_name, context={"form": form,
                                                                        "zone_status": try_zone_login(access_token)})
                else:
                    refresh_check, new_access_token = get_access_token(refresh_token)
                    if refresh_check:
                        request.session['access_token'] = new_access_token
                        return render(request, self.template_name, context={"form": form,
                                                                            "zone_status": try_zone_login(new_access_token)})
                    else:
                        form = ZoneSmartLoginForm(request.GET)
                        return render(request, self.template_name, context={"form": form,
                                                                            "zone_status": False})
            case False:
                form = ZoneSmartLoginForm(request.GET)
                return render(request, self.template_name, context={"form": form,
                                                                    "zone_status": False})
