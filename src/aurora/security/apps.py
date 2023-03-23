from django.apps import AppConfig


class Config(AppConfig):
    name = "aurora.security"

    def ready(self):
        from django.contrib.contenttypes.models import ContentType
        from smart_admin.decorators import smart_register
        from smart_admin.smart_auth.admin import ContentTypeAdmin, PermissionAdmin

        from . import handlers  # noqa
        from . import admin, models

        smart_register(models.AuroraPermission)(PermissionAdmin)
        smart_register(models.Permission)(PermissionAdmin)
        smart_register(models.AuroraGroup)(admin.GroupAdmin)
        smart_register(models.AuroraUser)(admin.UserAdmin)
        smart_register(models.AuroraRole)(admin.AuroraRoleAdmin)
        smart_register(models.UserProfile)(admin.UserProfileAdmin)

        smart_register(ContentType)(ContentTypeAdmin)
