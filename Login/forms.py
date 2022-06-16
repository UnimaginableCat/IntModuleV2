from django import forms
from django.utils.translation import gettext_lazy as _


class LoginForm(forms.Form):
    address = forms.CharField(label=_('retail_address'), required=True,
                              widget=forms.TextInput(attrs={'placeholder': _('retail_address')}))
    api_key = forms.CharField(label=_('retail_api_key'), required=True,
                              widget=forms.TextInput(attrs={'placeholder': _('retail_api_key')}))