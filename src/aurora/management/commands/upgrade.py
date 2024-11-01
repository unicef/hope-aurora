"""
"""
import logging
from pathlib import Path

from django.core.cache import cache
from django.core.management import CommandError, call_command

import djclick as click
from redis.exceptions import LockError

from aurora import VERSION

logger = logging.getLogger(__name__)


class NotRunningInTTYException(Exception):
    pass


@click.command()  # noqa: C901
@click.option("-v", "--verbosity", default=1, help="verbosity")
@click.option(
    "--prompt/--no-input",
    default=False,
    is_flag=True,
    help="Do not prompt for parameters",
)
@click.option("--admin-email", "-e", default="", envvar="ADMIN_EMAIL", help="Admin email")
@click.option(
    "--admin-password",
    "-p",
    default="",
    envvar="ADMIN_PASSWORD",
    help="Admin password",
)
@click.option("--migrate/--no-migrate", default=True, is_flag=True, help="Run database migrations")
@click.option("--static/--no-static", default=True, is_flag=True, help="Collect static assets")
@click.option("--organization", default=None, envvar="DEFAULT_ORGANIZATION", help="Main Organization name")
def upgrade(admin_email, admin_password, static, migrate, prompt, verbosity, organization, **kwargs):
    from aurora.config import env
    from aurora.core.models import FlexForm, Organization, Project
    from aurora.registration.models import Registration

    extra = {"no_input": prompt, "verbosity": verbosity - 1, "stdout": None}
    click.echo("Run upgrade.. waiting for lock")
    try:
        with cache.lock(env("MIGRATION_LOCK_KEY"), timeout=60 * 10, blocking_timeout=2, version=VERSION):
            if migrate:
                if verbosity >= 1:
                    click.echo("Run migrations")
                call_command("migrate", **extra)
                call_command("create_extra_permissions")

            # ensure project/org
            click.echo("Set default Org/Project")
            UNICEF, __ = Organization.objects.get_or_create(slug="unicef", defaults={"name": organization})
            DEF, __ = Project.objects.get_or_create(slug="default-project", organization=UNICEF)

            Project.objects.filter(organization__isnull=True).update(organization=UNICEF)
            Registration.objects.filter(project__isnull=True).update(project=DEF)
            FlexForm.objects.filter(project__isnull=True).update(project=DEF)

            static_root = Path(env("STATIC_ROOT"))
            if not static_root.exists():
                static_root.mkdir(parents=True)
            print(f"STATIC_ROOT set to '{static_root}' ('{static_root.absolute()}')")
            if static:
                if verbosity >= 1:
                    click.echo("Run collectstatic")
                call_command("collectstatic", **extra)

            call_command("createinitialrevisions")

            if organization:
                from aurora.core.models import Organization

                org, __ = Organization.objects.get_or_create(name=organization)
                if FlexForm.objects.filter(project__isnull=True).exists():
                    prj, __ = org.projects.get_or_create(name="Default Project")
                    FlexForm.objects.filter(project__isnull=True).update(project=prj)

            if admin_email:
                from django.contrib.auth import get_user_model

                User = get_user_model()
                if User.objects.filter(is_superuser=True).exists():
                    print("Superuser already exists. Ignoring ADMIN_EMAIL")
                else:
                    username, __ = admin_email.split("@")
                    if User.objects.filter(username=username).exists():
                        print("User with this name already exists")
                    else:
                        try:
                            call_command(
                                "createsuperuser",
                                interactive=False,
                                username=username,
                                email=admin_email,
                                verbosity=verbosity,
                            )
                            u = User.objects.get(username=username)
                            u.set_password(admin_password)
                            u.save()
                        except CommandError:
                            raise

                import django
                from django.conf import settings
                from django.utils import translation

                django.setup()
                print(f"LANGUAGE_CODE: {settings.LANGUAGE_CODE}")
                print(f"LOCALE: {translation.to_locale(settings.LANGUAGE_CODE)}")
                translation.activate(settings.LANGUAGE_CODE)
                print("check_for_language", translation.check_for_language("settings.LANGUAGE_CODE"))
    except LockError as e:
        print(f"LockError: {e}")
