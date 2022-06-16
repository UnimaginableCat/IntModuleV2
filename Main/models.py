import json

import requests
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver
from django_celery_beat.models import PeriodicTask, IntervalSchedule
from enumchoicefield import EnumChoiceField
from django.utils import timezone
from IntModuleV2.enums import TimeInterval, TaskStatus


# class Checker(models.Model):
#     class Meta:
#         abstract = True
#
#     retail_address = models.CharField(max_length=70, blank=False)
#     retail_api_key = models.CharField(max_length=100, blank=False)
#     access_token = models.TextField(null=True)
#     refresh_token = models.TextField(null=True)
#     period = EnumChoiceField(TimeInterval, default=TimeInterval.one_min)
#     status = EnumChoiceField(TaskStatus, default=TaskStatus.active)
#     products = models.TextField(null=True)
#     task = models.OneToOneField(
#         PeriodicTask,
#         on_delete=models.CASCADE,
#         blank=True,
#         null=True
#     )
#
#     def delete(self, *args, **kwargs):
#         if self.task is not None:
#             self.task.delete()
#         return super(self.__class__, self).delete(*args, **kwargs)
#
#     @property
#     def interval_schedule(self):
#         match self.period:
#             case TimeInterval.one_min:
#                 return IntervalSchedule.objects.get(every=1, period='minutes')
#             case TimeInterval.five_minutes:
#                 return IntervalSchedule.objects.get(every=5, period='minutes')
#             case TimeInterval.fifteen_minutes:
#                 return IntervalSchedule.objects.get(every=15, period='minutes')
#             case TimeInterval.one_hour:
#                 return IntervalSchedule.objects.get(every=1, period='hours')
#             case TimeInterval.one_day:
#                 return IntervalSchedule.objects.get(every=1, period='days')


class QuantityChecker(models.Model):
    retail_address = models.CharField(max_length=70, blank=False)
    retail_api_key = models.CharField(max_length=100, blank=False)
    access_token = models.TextField(null=True)
    refresh_token = models.TextField(null=True)
    period = EnumChoiceField(TimeInterval, default=TimeInterval.one_min)
    status = EnumChoiceField(TaskStatus, default=TaskStatus.active)
    products = models.TextField(null=True)
    task = models.OneToOneField(
        PeriodicTask,
        on_delete=models.CASCADE,
        blank=True,
        null=True
    )

    def delete(self, *args, **kwargs):
        if self.task is not None:
            self.task.delete()
        return super(self.__class__, self).delete(*args, **kwargs)

    @property
    def interval_schedule(self):
        match self.period:
            case TimeInterval.one_min:
                return IntervalSchedule.objects.get(every=1, period='minutes')
            case TimeInterval.five_minutes:
                return IntervalSchedule.objects.get(every=5, period='minutes')
            case TimeInterval.fifteen_minutes:
                return IntervalSchedule.objects.get(every=15, period='minutes')
            case TimeInterval.one_hour:
                return IntervalSchedule.objects.get(every=1, period='hours')
            case TimeInterval.one_day:
                return IntervalSchedule.objects.get(every=1, period='days')

    def setup_task(self):
        self.task = PeriodicTask.objects.create(
            name=f"Task-quantity-update: {self.retail_address} #{QuantityChecker.objects.filter(retail_address=self.retail_address).count().__str__()}",
            task='update_products_quantity',
            interval=self.interval_schedule,
            args=json.dumps([self.retail_address, self.retail_api_key, self.access_token, self.refresh_token,
                             self.products]),
            start_time=timezone.now()
        )
        self.save()


class PriceChecker(models.Model):
    retail_address = models.CharField(max_length=70, blank=False)
    retail_api_key = models.CharField(max_length=100, blank=False)
    access_token = models.TextField(null=True)
    refresh_token = models.TextField(null=True)
    period = EnumChoiceField(TimeInterval, default=TimeInterval.one_min)
    status = EnumChoiceField(TaskStatus, default=TaskStatus.active)
    products = models.TextField(null=True)
    task = models.OneToOneField(
        PeriodicTask,
        on_delete=models.CASCADE,
        blank=True,
        null=True
    )

    def delete(self, *args, **kwargs):
        if self.task is not None:
            self.task.delete()
        return super(self.__class__, self).delete(*args, **kwargs)

    @property
    def interval_schedule(self):
        match self.period:
            case TimeInterval.one_min:
                return IntervalSchedule.objects.get(every=1, period='minutes')
            case TimeInterval.five_minutes:
                return IntervalSchedule.objects.get(every=5, period='minutes')
            case TimeInterval.fifteen_minutes:
                return IntervalSchedule.objects.get(every=15, period='minutes')
            case TimeInterval.one_hour:
                return IntervalSchedule.objects.get(every=1, period='hours')
            case TimeInterval.one_day:
                return IntervalSchedule.objects.get(every=1, period='days')

    def setup_task(self):
        self.task = PeriodicTask.objects.create(
            name=f"Task-price-update: {self.retail_address} #{PriceChecker.objects.filter(retail_address=self.retail_address).count().__str__()}",
            task='update_products_price',
            interval=self.interval_schedule,
            args=json.dumps([self.retail_address, self.retail_api_key, self.access_token, self.refresh_token,
                             self.products]),
            start_time=timezone.now()
        )
        self.save()


@receiver(post_save, sender=QuantityChecker)
def create_or_update_periodic_task(sender, instance, created, **kwargs):
    if created:
        instance.setup_task()
    else:
        if instance.task is not None:
            instance.task.enabled = instance.status == TaskStatus.active


@receiver(post_save, sender=PriceChecker)
def create_or_update_periodic_task(sender, instance, created, **kwargs):
    if created:
        instance.setup_task()
    else:
        if instance.task is not None:
            instance.task.enabled = instance.status == TaskStatus.active


class ZoneSmartProduct:
    def __init__(self, sku, quantity, price, product_code, main_image, ext_images, access_token, attributes):
        self.sku = sku
        self.quantity = quantity
        self.price = price
        if product_code is None:
            self.product_code = "pcode"
        else:
            self.product_code = product_code
        self.condition = "NEW"

        self.attributes = list()
        if attributes is not None:
            for key in attributes:
                temp = {
                    'name': key,
                    'value': attributes[key]
                }
                self.attributes.append(temp)
        #    temp = ['name':]
        #    self.attributes.
        # self.main_image = self.upload_image(main_image, access_token)
        # self.extra_images = []
        # for image in ext_images:
        #    self.extra_images.append(self.upload_image(image, access_token))

    def upload_image(self, image, access_token):
        header = {
            'Content-Type': 'application/json',
            'Authorization': 'JWT ' + access_token
        }
        data = {
            "url": image,
        }
        response = requests.post("https://api.zonesmart.com/v1/zonesmart/image/", headers=header,
                                 json=data)
        image_url = json.loads(response.text)['id']
        return image_url


class ZoneSmartListing:
    def __init__(self, title, desc, list_sku, cat, cat_name, brand, products: list, main_image, ext_images,
                 access_token):
        self.title = title
        if desc == "":
            self.description = "Exported from RetailCRM"
        else:
            self.description = desc
        self.listing_sku = list_sku
        # self.category = cat
        self.category_name = cat_name
        self.brand = brand
        self.currency = "RUB"
        self.products = products
        self.main_image = self.upload_image(main_image, access_token)
        self.extra_images = []
        for image in ext_images:
            if image == main_image:
                continue
            else:
                self.extra_images.append(self.upload_image(image, access_token))

    def upload_image(self, image, access_token):
        header = {
            'Content-Type': 'application/json',
            'Authorization': 'JWT ' + access_token
        }
        data = {
            "url": image,
        }
        response = requests.post("https://api.zonesmart.com/v1/zonesmart/image/", headers=header,
                                 json=data)
        image_url = json.loads(response.text)['id']
        return image_url

    def to_json(self):
        return json.dumps(self, default=lambda o: o.__dict__, ensure_ascii=False)