from .. import env

SOCIAL_AUTH_AZUREAD_TENANT_OAUTH2_SECRET = env.str("AZURE_CLIENT_SECRET")
SOCIAL_AUTH_AZUREAD_TENANT_OAUTH2_TENANT_ID = env("AZURE_TENANT_ID")
SOCIAL_AUTH_AZUREAD_TENANT_OAUTH2_KEY = env.str("AZURE_CLIENT_KEY")
SOCIAL_AUTH_RESOURCE = "https://graph.microsoft.com/"
SOCIAL_AUTH_ADMIN_USER_SEARCH_FIELDS = [
    "username",
    "first_name",
    "last_name",
    "email",
]

SOCIAL_AUTH_JSONFIELD_ENABLED = True
SOCIAL_AUTH_PIPELINE = (
    "aurora.core.authentication.social_details",
    "social_core.pipeline.social_auth.social_uid",
    "social_core.pipeline.social_auth.auth_allowed",
    "social_core.pipeline.social_auth.social_user",
    "social_core.pipeline.user.get_username",
    "aurora.core.authentication.require_email",
    "social_core.pipeline.social_auth.associate_by_email",
    "aurora.core.authentication.create_user",
    "social_core.pipeline.social_auth.associate_user",
    "social_core.pipeline.social_auth.load_extra_data",
    "aurora.core.authentication.user_details",
    "aurora.core.authentication.redir_to_form",
)
SOCIAL_AUTH_AZUREAD_B2C_OAUTH2_USER_FIELDS = [
    "email",
    "fullname",
]

SOCIAL_AUTH_AZUREAD_B2C_OAUTH2_SCOPE = [
    "openid",
    "email",
    "profile",
]

SOCIAL_AUTH_SANITIZE_REDIRECTS = True
SOCIAL_AUTH_JWT_LEEWAY = env("JWT_LEEWAY")
