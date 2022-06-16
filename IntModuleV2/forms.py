from django import forms
from django.core import validators
from django.core.validators import MinValueValidator

from IntModuleV2.enums import TimeInterval


class LoginForm(forms.Form):
    address = forms.CharField(label="Адрес", required=True, widget=forms.TextInput(attrs={'placeholder': 'Address'}))
    api_key = forms.CharField(label="Ключ API", required=True, widget=forms.TextInput(attrs={'placeholder': 'ApiKey'}))


class ZoneSmartLoginForm(forms.Form):
    email = forms.CharField(label="Email", required=True, widget=forms.TextInput(attrs={'placeholder': 'Email'}),
                            initial="")
    password = forms.CharField(label="Password", required=True,
                               widget=forms.TextInput(attrs={'placeholder': 'Password'}), initial="")


CHOICES = [
    (1, 'Active'),
    (0, 'Not Active')
]
PRICE_SYNC_CHOICES = [
    (1, 'Yes'),
    (0, 'No')
]

time_intervals = [
    ('one_min', '1 Minute'),
    ('five_minutes', '5 Minutes'),
    ('fifteen_minutes', '15 Minutes'),
    ('one_hour', '1 Hour'),
    ('one_day', '1 Day')
]


class ExportProductsForm(forms.Form):

    def __init__(self, choices, *args, **kwargs):
        super(ExportProductsForm, self).__init__(*args, **kwargs)
        self.fields['groups'] = forms.MultipleChoiceField(label="Product categories:",
                                                          widget=forms.CheckboxSelectMultiple,
                                                          choices=choices,
                                                          required=True)

    active = forms.CharField(label='Which products to export?',
                             widget=forms.RadioSelect(choices=CHOICES, attrs={'class': 'active_filter'}))
    min_quantity = forms.IntegerField(label="Minimal quantity of product:",
                                      validators=[validators.MinValueValidator(0)],
                                      widget=forms.NumberInput(attrs={'min': 0}))
    groups = forms.MultipleChoiceField(label="Product categories:",
                                       widget=forms.CheckboxSelectMultiple,
                                       # choices=OPTIONS,
                                       required=True)
    quantity_check_period = forms.CharField(label='Period of products quantity synchronization:',
                                            widget=forms.Select(choices=time_intervals))
    price_sync = forms.CharField(label='Do you want to synchronize prices?',
                                 widget=forms.RadioSelect(choices=PRICE_SYNC_CHOICES, attrs={'class': 'active_filter',
                                                                                             'id': 'price_sync'}),
                                 initial=0)

    price_check_period = forms.CharField(label='Period of products price synchronization:',
                                         widget=forms.Select(choices=time_intervals),
                                         required=False)
