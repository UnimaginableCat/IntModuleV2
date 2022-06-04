from django.http import HttpResponseRedirect
from django.shortcuts import redirect

from IntModuleV2.views import delete_session
from Login.views import Authenticator


auth_helper = Authenticator()


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

class RetailAuthCheckMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        match request.path:
            case "/login" | "/":
                retail_cookie_check, address, api_key = check_retail_cookies(request)
                if retail_cookie_check:
                    retail_login_check = auth_helper.try_retail_login(address, api_key)
                    if retail_login_check:
                        return redirect("/zone_account")
                    else:
                        delete_session(request)
                        return redirect("/login")
            case "/zone_account" | "/module_settings":
                retail_cookie_check, address, api_key = check_retail_cookies(request)
                if retail_cookie_check:
                    retail_login_check = auth_helper.try_retail_login(address, api_key)
                    if not retail_login_check:
                        delete_session(request)
                        return redirect("/login")
                else:
                    return HttpResponseRedirect("/login")

        response = self.get_response(request)

        return response
