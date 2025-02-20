from django.apps import AppConfig


class AuroraAdminConfig(AppConfig):
    default = False
    name = "aurora.administration"

    def ready(self):
        super().ready()
        from django.contrib.admin import site

        from smart_admin.console import (
            panel_email,
            panel_error_page,
            panel_migrations,
            panel_redis,
            panel_sentry,
            panel_sysinfo,
        )

        from .panels import panel_dumpdata, panel_loaddata, panel_sql

        site.register_panel(panel_loaddata)
        site.register_panel(panel_dumpdata)
        site.register_panel(panel_migrations)
        site.register_panel(panel_sysinfo)
        site.register_panel(panel_email)
        site.register_panel(panel_sentry)
        site.register_panel(panel_error_page)
        site.register_panel(panel_redis)
        site.register_panel(panel_sql)
