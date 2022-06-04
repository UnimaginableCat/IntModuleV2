import json
import string

import requests
import retailcrm
from django.http import HttpResponsePermanentRedirect
from django.shortcuts import render
from django.views import View

from IntModuleV2.forms import ZoneSmartLoginForm, ExportProductsForm
from Login.views import auth_helper


def get_access_token(refresh_token):
    header = {
        'Content-Type': 'application/json',
    }
    data = {
        "refresh": refresh_token,
    }
    response = requests.post("https://api.zonesmart.com/v1/auth/jwt/refresh/", headers=header, json=data)
    converted_response = json.loads(response.text)
    access_token = converted_response['access']
    return access_token


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
        return True, email, password, refresh_token


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


def try_zone_login(access_token):
    header = {
        'Content-Type': 'application/json',
        'Authorization': 'JWT ' + access_token
    }
    r = requests.get("https://api.zonesmart.com/v1/zonesmart/marketplace/", headers=header)
    if r.status_code == 200:
        return True
    else:
        return False

class ZoneSmartProduct:
    def __init__(self, sku, quantity, price, product_code, main_image, extra_images):
        self.sku = sku
        self.quantity = quantity
        self.price = price
        self.product_code = product_code
        self.condition = "NEW"
        self.main_image = main_image
        self.extra_images = extra_images


class ZoneSmartListing:
    def __init__(self, title, desc, list_sku, cat, cat_name, brand, products: list):
        self.title = title
        self.description = desc
        self.listing_sku = list_sku
        self.category = cat
        self.category_name = cat_name
        self.brand = brand
        self.currency = "RUB"
        self.products = products


class RetailCRMHelper:
    def __init__(self):
        self.address = None
        self.api_key = None
        self.client = None

    def init_and_setup(self, address, api_key):
        self.address = address
        self.api_key = api_key
        self.client = retailcrm.v5(self.address, self.api_key)

    def get_products(self, dict_groups, active=0, min_quantity=0, groups=None):
        if groups is None:
            groups = []
        if not groups:
            product_filter = {
                'active': active,
                'minQuantity': min_quantity,
            }
        else:
            product_filter = {
                'active': active,
                'minQuantity': min_quantity,
                'groups': groups,
            }
        products = []
        total_count = self.client.products(product_filter).get_response()['pagination']['totalCount']
        if total_count != 0:
            total_page_count = self.client.products(product_filter).get_response()['pagination']['totalPageCount']
            #test = self.client.products(product_filter).get_response()
            #print(test)

            for i in range(1, total_page_count + 1):
                products_query = self.client.products(product_filter, 20, i).get_response()['products']
                #print(products_query)
                for product in products_query:
                    #print(product)
                    offers = []
                    for offer in product['offers']:
                        #print(offer)

                        new_offer = ZoneSmartProduct(offer.get('id'),
                                                     offer.get('quantity'),
                                                     offer.get('price'),
                                                     offer.get('barcode'),
                                                     product.get('imageUrl'),
                                                     offer.get('images'))
                        offers.append(new_offer)
                    new_listing = ZoneSmartListing(product.get('name'),
                                                   product.get('description'),
                                                   product.get('id'),
                                                   product['groups'][0]['externalId'],
                                                   dict_groups.get(product['groups'][0]['externalId']),
                                                   product.get('manufacturer'),
                                                   offers)
                    products.append(new_listing)
        return products

    def get_product_groups(self):
        groups = dict()

        groups_filter = {'active': 1}

        total_page_count = self.client.product_groups(groups_filter).get_response()['pagination']['totalPageCount']
        for i in range(1, total_page_count + 1):
            group_query = self.client.product_groups(groups_filter, 20, i).get_response()['productGroup']
            for group in group_query:
                groups[group['externalId']] = group['name']
        tuple_groups = [(k, v) for k, v in groups.items()]
        #Возвращаем группы в нужном виде, и в виде Dict
        return tuple_groups, groups


def init_retail_helper(request):
    address = request.session['address']
    api_key = request.session['api_key']
    retail_helper = RetailCRMHelper()
    retail_helper.init_and_setup(address, api_key)
    return retail_helper


class ExportProductsView(View):
    template_name = 'main_page/main_export_products.html'
    http_method_names = ['get', 'post']

    def post(self, request):
        retail_helper = init_retail_helper(request)
        choices, groups_dict = retail_helper.get_product_groups()
        form = ExportProductsForm(choices)

        active = request.POST.get('active')
        min_quantity = request.POST.get('min_quantity')
        groups = request.POST.getlist('groups')
        # Список продуктов для переноса
        products_to_export = retail_helper.get_products(groups_dict, active, min_quantity, groups)


        #print(products_to_export)
        zone_cookie_check, email, password = check_zone_cookies(request)
        if zone_cookie_check:
            return render(request, self.template_name,
                          context={'zone_status': auth_helper.create_zone_tokens(email, password),
                                   'form': form})
        else:
            return render(request, self.template_name,
                          context={'zone_status': False,
                                   'form': form})

    def get(self, request):
        retail_helper = init_retail_helper(request)
        choices, groups_dict = retail_helper.get_product_groups()
        #print(choices)
        form = ExportProductsForm(choices)
        zone_cookie_check, email, password = check_zone_cookies(request)
        if zone_cookie_check:
            return render(request, self.template_name,
                          context={'zone_status': auth_helper.create_zone_tokens(email, password),
                                   'form': form})
        else:
            return render(request, self.template_name,
                          context={'zone_status': False,
                                   'form': form})


class ZoneAccountView(View):
    template_name = 'main_page/main_zone_acc.html'
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
            request.session['refresh_token'] = access_token
            return render(request, "main_page/main_zone_acc.html", context={"form": form,
                                                                            "auth_state": zone_login_check,
                                                                            "zone_status": zone_login_check})
        else:
            return render(request, "main_page/main_zone_acc.html", context={"form": form,
                                                                            "auth_state": zone_login_check})

    def get(self, request):
        zone_cookie_check, email, password, refresh_token = check_zone_cookies(request)
        if zone_cookie_check:
            access_token = get_access_token(refresh_token)
            zone_login_check = try_zone_login(access_token)
            if zone_login_check:
                auth_helper.set_zone_pass(password)
                auth_helper.set_zone_email(email)
                form = ZoneSmartLoginForm(initial={'email': email,
                                                   'password': password}, auto_id=False)
                return render(request, "main_page/main_zone_acc.html", context={"form": form,
                                                                                "zone_status": zone_login_check})
            else:
                form = ZoneSmartLoginForm(request.GET)
                return render(request, "main_page/main_zone_acc.html", context={"form": form,
                                                                                "zone_status": zone_login_check})
        else:
            form = ZoneSmartLoginForm(request.GET)
            return render(request, "main_page/main_zone_acc.html", context={"form": form,
                                                                            "zone_status": False})
