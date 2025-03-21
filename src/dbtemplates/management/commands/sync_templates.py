import os

from django.contrib.sites.models import Site
from django.core.management.base import BaseCommand, CommandError
from django.template.loader import _engine_list
from django.template.utils import get_app_template_dirs

from dbtemplates.models import Template

ALWAYS_ASK, FILES_TO_DATABASE, DATABASE_TO_FILES = ("0", "1", "2")

DIRS = []
for engine in _engine_list():
    DIRS.extend(engine.dirs)
app_template_dirs = get_app_template_dirs("templates")


class Command(BaseCommand):
    help = "Syncs file system templates with the database bidirectionally."

    def add_arguments(self, parser):
        parser.add_argument(
            "-e",
            "--ext",
            dest="ext",
            action="store",
            default="html",
            help="extension of the files you want to sync with the database [default: %default]",
        )
        parser.add_argument(
            "-f",
            "--force",
            action="store_true",
            dest="force",
            default=False,
            help="overwrite existing database templates",
        )
        parser.add_argument(
            "-o",
            "--overwrite",
            action="store",
            dest="overwrite",
            default="0",
            help="'0' - ask always, '1' - overwrite database "
            "templates from template files, '2' - overwrite "
            "template files from database templates",
        )
        parser.add_argument(
            "-a",
            "--app-first",
            action="store_true",
            dest="app_first",
            default=False,
            help="look for templates in applications directories before project templates",
        )
        parser.add_argument(
            "-d",
            "--delete",
            action="store_true",
            dest="delete",
            default=False,
            help="Delete templates after syncing",
        )

    def handle(self, **options):  # noqa C901
        extension = options.get("ext")
        force = options.get("force")
        overwrite = options.get("overwrite")
        app_first = options.get("app_first")
        delete = options.get("delete")

        if not extension.startswith("."):
            extension = ".%s" % extension

        try:
            site = Site.objects.get_current()
        except Exception:
            raise CommandError(
                "Please make sure to have the sites contrib app installed and setup with a site object"
            ) from None

        if app_first:
            tpl_dirs = app_template_dirs + DIRS
        else:
            tpl_dirs = DIRS + app_template_dirs
        templatedirs = [d for d in tpl_dirs if os.path.isdir(d)]

        for templatedir in templatedirs:
            for dirpath, _, filenames in os.walk(templatedir):
                for f in [f for f in filenames if f.endswith(extension) and not f.startswith(".")]:
                    path = os.path.join(dirpath, f)
                    name = path.split(templatedir)[1].removeprefix("/")
                    try:
                        t = Template.on_site.get(name__exact=name)
                    except Template.DoesNotExist:
                        if not force:
                            confirm = input(
                                "\nA '%s' template doesn't exist in the "
                                "database.\nCreate it with '%s'?"
                                " (y/[n]): "
                                "" % (name, path)
                            )
                        if force or confirm.lower().startswith("y"):
                            with open(path, encoding="utf-8") as f1:
                                t = Template(name=name, content=f1.read())
                            t.save()
                            t.sites.add(site)
                    else:
                        while 1:
                            if overwrite == ALWAYS_ASK:
                                confirm = input(
                                    "\n%(template)s exists in the database.\n"
                                    "(1) Overwrite %(template)s with '%(path)s'\n"
                                    "(2) Overwrite '%(path)s' with %(template)s\n"
                                    "Type 1 or 2 or press <Enter> to skip: " % {"template": t.__repr__(), "path": path}
                                )
                            else:
                                confirm = overwrite
                            if confirm in ("", FILES_TO_DATABASE, DATABASE_TO_FILES):
                                if confirm == FILES_TO_DATABASE:
                                    with open(path, encoding="utf-8") as f2:
                                        t.content = f2.read()
                                        t.save()
                                        t.sites.add(site)
                                    if delete:
                                        try:
                                            os.remove(path)
                                        except OSError:
                                            raise CommandError("Couldn't delete %s" % path) from None
                                elif confirm == DATABASE_TO_FILES:
                                    with open(path, "w", encoding="utf-8") as f3:
                                        f3.write(t.content)
                                    if delete:
                                        t.delete()
                                break
