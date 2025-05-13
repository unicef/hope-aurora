from django.http import HttpRequest

from aurora.security.models import User

class AuthHttpRequest(HttpRequest):
    user: User
