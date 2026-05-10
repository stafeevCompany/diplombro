from django import forms

from .models import *

class LoginForm(forms.Form):
    phone = forms.CharField(max_length=15)
    password = forms.CharField(widget=forms.PasswordInput)

class RegistrationForm(forms.Form):
    lastname = forms.CharField(max_length=15)
    firstname = forms.CharField(max_length=15)
    patronymic = forms.CharField(max_length=15)
    phone = forms.CharField(max_length=15)
    password = forms.CharField(widget=forms.PasswordInput)
    birthday = forms.DateField(widget=forms.DateInput)


class QuantityForm(forms.Form):
    quantity = forms.IntegerField(min_value=1)