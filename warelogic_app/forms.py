from django.contrib.auth.forms import PasswordChangeForm
from django.contrib.auth.models import User
from django import forms
...
class PasswordChangingForm(PasswordChangeForm):
    class Meta:
        model = User
        fields = ["old_password",'new_password1', 'new_password2']

class ProductSearchForm(forms.Form):
    search_term = forms.CharField(max_length=50, required=True, label = "Enter Partnumber, productcode or barcode:")

class BinSearchForm(forms.Form):
    search_term = forms.CharField(max_length=20, required=True, label = "Enter bin location:")

