from django.shortcuts import redirect


def delete_session(request):
    try:
        del request.session['address']
        del request.session['api_key']
    except KeyError:
        pass


def logout(request):
    if request.method == "GET":
        delete_session(request)
        return redirect("/login")
