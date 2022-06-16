from django.contrib import admin

# Register your models here.
from Main.models import PriceChecker, QuantityChecker

admin.site.register(QuantityChecker)
admin.site.register(PriceChecker)
