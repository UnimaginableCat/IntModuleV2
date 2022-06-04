import json

import requests
import retailcrm
from django.http import HttpResponsePermanentRedirect
from django.shortcuts import render, redirect
from django.views import View

from IntModuleV2.forms import LoginForm


class Authenticator:  # Класс помогающий с входом

    def __init__(self):
        self.password = ""
        self.email = ""
        self.address = ""
        self.api_key = ""

    def set_address(self, address):
        self.address = address

    def set_api_key(self, api_key):
        self.api_key = api_key

    def set_zone_email(self, email):
        self.email = email

    def set_zone_pass(self, password):
        self.password = password

    def try_retail_login(self, address, api_key):
        client = retailcrm.v5(address, api_key)
        try:
            login_state = client.product_groups({'active': '1'}).get_response()['success']
        except Exception:
            login_state = False
        return login_state

    def create_zone_tokens(self, email, password):
        header = {
            'Content-Type': 'application/json',
        }
        data = {
            "email": email,
            "password": password
        }
        r = requests.post("https://api.zonesmart.com/v1/auth/jwt/create/", headers=header, json=data)
        #print(r.text)
        tokens = json.loads(r.text)
        access = tokens['access']
        refresh = tokens['refresh']
        status = r.status_code
        if status == 200:
            return True, access, refresh
        else:
            return False, "", ""


auth_helper = Authenticator()


class LoginView(View):
    template_name = 'account/Login.html'
    http_method_names = ['get', 'post']

    def post(self, request):
        form = LoginForm(request.POST)
        address = request.POST.get("address")
        api_key = request.POST.get("api_key")

        auth_check = auth_helper.try_retail_login(address, api_key)
        if auth_check:  # Если вход удачный, то запоминаем адресс и ключ в кукис
            request.session['address'] = address
            request.session['api_key'] = api_key
            return redirect("/zone_account")
        else:
            return render(request, "account/Login.html", context={'login_state': auth_check, "form": form})

    def get(self, request):
        form = LoginForm(request.GET)  # Получаем форму
        return render(request, "account/Login.html", context={"form": form})