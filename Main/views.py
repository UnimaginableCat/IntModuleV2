import json
import string

import jsonpickle as jsonpickle
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
        if product_code is None:
            self.product_code = "pcode"
        else:
            self.product_code = product_code
        self.condition = "NEW"
        self.main_image = main_image
        self.extra_images = extra_images
        #self.attributes = {"name": "testName",
        #                   "value":"testValue"}


class ZoneSmartListing:
    def __init__(self, title, desc, list_sku, cat, cat_name, brand, products: list):
        self.title = title
        if desc == "":
            self.description = "Exported from RetailCRM"
        else:
            self.description = desc
        self.listing_sku = list_sku
        #self.category = cat
        self.category_name = cat_name
        self.brand = brand
        self.currency = "RUB"
        self.products = products

    def to_json(self):
        return json.dumps(self, default=lambda o: o.__dict__,ensure_ascii=False)


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

#Ура почти заработало
def zone_create_listing(products, access_token):
    header = {
        'Content-Type': 'application/json',
        'Authorization': 'JWT ' + access_token
    }
    results = dict()
    for product in products:
        json_product = product.to_json()
        correct_json = json.loads(json_product)
        response = requests.post("https://api.zonesmart.com/v1/zonesmart/listing/", headers=header,
                                 json=correct_json)
        results[product.title] = response.status_code
    return results


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
        products_to_export = retail_helper.get_products(groups_dict, active, min_quantity, groups)
        print(products_to_export)

        zone_cookie_check, email, password, refresh_token, access_token = check_zone_cookies(request)
        match zone_cookie_check:
            case True:
                access_token_check = try_zone_login(access_token)
                if access_token_check:
                    zone_create_listing(products_to_export, access_token)
                    return render(request, self.template_name,
                                  context={"form": form, "zone_status": try_zone_login(access_token)})
                else:
                    refresh_check, new_access_token = get_access_token(refresh_token)
                    if refresh_check:
                        request.session['access_token'] = new_access_token
                        zone_create_listing(products_to_export, new_access_token)
                        return render(request, self.template_name,
                                      context={"form": form, "zone_status": try_zone_login(new_access_token)})
                    else:
                        return render(request, self.template_name, context={"form": form,
                                                                            "zone_status": False,
                                                                            "export_error": True})
            case False:
                return render(request, self.template_name,
                              context={'zone_status': False,
                                       'form': form})



    def get(self, request):
        retail_helper = init_retail_helper(request)
        choices, groups_dict = retail_helper.get_product_groups()
        #print(choices)
        form = ExportProductsForm(choices)
        zone_cookie_check, email, password, refresh_token, access_token = check_zone_cookies(request)
        if zone_cookie_check:
            return render(request, self.template_name,
                          context={'zone_status': try_zone_login(access_token),
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
            request.session['refresh_token'] = refresh_token
            return render(request, "main_page/main_zone_acc.html", context={"form": form,
                                                                            "auth_state": zone_login_check,
                                                                            "zone_status": zone_login_check})
        else:
            return render(request, "main_page/main_zone_acc.html", context={"form": form,
                                                                            "auth_state": zone_login_check})

    def get(self, request):
        zone_cookie_check, email, password, refresh_token, access_token = check_zone_cookies(request)
        form = ZoneSmartLoginForm(initial={'email': email,
                                           'password': password}, auto_id=False)
        match zone_cookie_check:
            case True:
                access_token_check = try_zone_login(access_token)
                if access_token_check:
                    return render(request, "main_page/main_zone_acc.html", context={"form": form,
                                                                                    "zone_status": try_zone_login(
                                                                                        access_token)})
                else:
                    refresh_check, new_access_token = get_access_token(refresh_token)
                    if refresh_check:
                        request.session['access_token'] = new_access_token
                        return render(request, "main_page/main_zone_acc.html", context={"form": form,
                                                                                        "zone_status": try_zone_login(
                                                                                            new_access_token)})
                    else:
                        form = ZoneSmartLoginForm(request.GET)
                        return render(request, "main_page/main_zone_acc.html", context={"form": form,
                                                                                        "zone_status": False})
            case False:
                form = ZoneSmartLoginForm(request.GET)
                return render(request, "main_page/main_zone_acc.html", context={"form": form,
                                                                                "zone_status": False})
