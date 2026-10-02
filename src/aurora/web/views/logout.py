from django.contrib.auth.views import LogoutView
from django.urls import reverse
from rest_framework.request import Request
from social_django.models import UserSocialAuth


def authenticated_via_sso(user: object) -> bool:
    """Whether this login came from an identity provider rather than a local password.

    social_django records an association for every federated login, which is what distinguishes a
    session that can be closed again on the provider's side from one that is entirely local.
    """
    return bool(user.is_authenticated and UserSocialAuth.objects.filter(user=user).exists())


class RegistrarLogoutView(LogoutView):
    """Terminate the local session, and the identity provider's session too when there is one.

    Logging out of Aurora does not log the user out of Azure AD, so a federated user who logs out
    is silently signed straight back in on the next request. Handing those users on to the
    provider's end-session endpoint is what makes logout mean what the user expects.

    The local session is flushed first, so the browser is already anonymous by the time the
    provider redirects back; that is why settings.LOGOUT_URL points at the index rather than here.
    """

    def dispatch(self, request: Request, *args, **kwargs) -> "object":
        self.sso = authenticated_via_sso(request.user)
        return super().dispatch(request, *args, **kwargs)

    def get_default_redirect_url(self) -> str:
        if self.sso:
            return reverse("unicef-logout")
        return super().get_default_redirect_url()
