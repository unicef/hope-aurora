from django import forms
from django.contrib.auth.forms import AuthenticationForm, UsernameField
from django.contrib.auth.views import LoginView
from django.http import HttpResponseRedirect
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from django.views import View

CSS_CLASS = "shadow appearance-none border rounded w-full py-2 px-3 my-1 cursor-pointer"


class RegistrarAuthenticationForm(AuthenticationForm):
    username = UsernameField(widget=forms.TextInput(attrs={"autofocus": True, "class": CSS_CLASS}))
    password = forms.CharField(
        label=_("Password"),
        strip=False,
        widget=forms.PasswordInput(attrs={"autocomplete": "current-password", "class": CSS_CLASS}),
    )


class LoginRouter(View):
    def get(self, request):
        url = "/"
        if requested_form := request.COOKIES.get("aurora_form", None):
            url = reverse("register", args=[requested_form])

        return HttpResponseRedirect(url)


class RegistrarLoginView(LoginView):
    template_name = "registration/login.html"
    form_class = RegistrarAuthenticationForm
