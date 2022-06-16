from attr import validators
from django import forms
from django.utils.translation import gettext_lazy as _


class ZoneSmartLoginForm(forms.Form):
    email = forms.CharField(label="Email", required=True, widget=forms.TextInput(attrs={'placeholder': 'Email'}),
                            initial="")
    password = forms.CharField(label=_('password'), required=True,
                               widget=forms.TextInput(attrs={'placeholder': _('password')}), initial="")


CHOICES = [
    (1, _('Active')),
    (0, _('Not Active'))
]
PRICE_SYNC_CHOICES = [
    (1, _('Yes')),
    (0, _('No'))
]

time_intervals = [
    ('one_min', _('1 Minute')),
    ('five_minutes', _('5 Minutes')),
    ('fifteen_minutes', _('15 Minutes')),
    ('one_hour', _('1 Hour')),
    ('one_day', _('1 Day'))
]


class ExportProductsForm(forms.Form):

    def __init__(self, choices, *args, **kwargs):
        super(ExportProductsForm, self).__init__(*args, **kwargs)
        self.fields['groups'] = forms.MultipleChoiceField(label=_("Product categories:"),
                                                          widget=forms.CheckboxSelectMultiple,
                                                          choices=choices,
                                                          required=True)

    active = forms.CharField(label=_('Which products to export?'),
                             widget=forms.RadioSelect(choices=CHOICES, attrs={'class': 'active_filter'}))
    min_quantity = forms.IntegerField(label=_("Minimal quantity of product:"),
                                      widget=forms.NumberInput(attrs={'min': 0}))
    groups = forms.MultipleChoiceField(label=_("Product categories:"),
                                       widget=forms.CheckboxSelectMultiple,
                                       # choices=OPTIONS,
                                       required=True)
    quantity_check_period = forms.CharField(label=_('Period of products quantity synchronization:'),
                                            widget=forms.Select(choices=time_intervals))
    price_sync = forms.CharField(label=_('Do you want to synchronize prices?'),
                                 widget=forms.RadioSelect(choices=PRICE_SYNC_CHOICES, attrs={'class': 'active_filter',
                                                                                             'id': 'price_sync'}),
                                 initial=0)

    price_check_period = forms.CharField(label=_('Period of products price synchronization:'),
                                         widget=forms.Select(choices=time_intervals),
                                         required=False)
