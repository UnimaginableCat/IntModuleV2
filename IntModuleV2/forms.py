from django import forms
from django.core import validators
from django.core.validators import MinValueValidator


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
                                       #choices=OPTIONS,
                                       required=True)
