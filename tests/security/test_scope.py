from django.contrib.auth.models import AnonymousUser

from aurora.security.scope import RoleScope, get_role_scope


def test_anonymous_user_has_no_scope():
    scope = get_role_scope(AnonymousUser())
    assert scope == RoleScope(frozenset(), frozenset(), frozenset(), unlimited=False)
