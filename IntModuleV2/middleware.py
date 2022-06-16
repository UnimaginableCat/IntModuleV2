from django.http import HttpResponseRedirect
from django.shortcuts import redirect

from IntModuleV2.views import delete_session
from Login.views import Authenticator
from Main.views import check_zone_cookies, try_zone_login, get_access_token, check_retail_cookies

auth_helper = Authenticator()


class ZoneAuthCheckMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        match request.path:
            case "/export_products":
                zone_cookie_check, email, password, refresh_token, access_token = check_zone_cookies(request)
                if not zone_cookie_check:
                    return redirect("/zone_account")
                access_token_check = try_zone_login(access_token)
                if not access_token_check:
                    refresh_check, new_access_token = get_access_token(refresh_token)
                    if not refresh_check:
                        return redirect("/zone_account")
                    request.session['access_token'] = new_access_token

        response = self.get_response(request)

        return response


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
            case "/zone_account" | "/export_products":
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
