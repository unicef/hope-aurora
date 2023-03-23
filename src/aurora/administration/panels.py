import io
import json
import logging
import tempfile
from pathlib import Path

import sqlparse
from concurrency.api import disable_concurrency
from django.contrib import messages
from django.core.exceptions import PermissionDenied
from django.core.management import call_command
from django.db import DEFAULT_DB_ALIAS, connections
from django.http import JsonResponse
from django.shortcuts import render

from .. import VERSION
from ..core.utils import is_root
from ..security.models import UserProfile
from .forms import ExportForm, ImportForm, SQLForm

logger = logging.getLogger(__name__)

QUICK_SQL = {
    "Show Tables": "SELECT * FROM information_schema.tables;",
    "Show Indexes": "SELECT tablename, indexname, indexdef FROM pg_indexes "
    "WHERE schemaname='public' ORDER BY tablename, indexname;",
    "Describe Table": "SELECT * FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_NAME=[table_name];",
    "Show Contraints": """SELECT con.*
       FROM pg_catalog.pg_constraint con
            INNER JOIN pg_catalog.pg_class rel
                       ON rel.oid = con.conrelid
            INNER JOIN pg_catalog.pg_namespace nsp
                       ON nsp.oid = connamespace;""",
}


def panel_loaddata(self, request):
    context = self.each_context(request)
    context["title"] = "Loaddata"
    if request.method == "POST":
        form = ImportForm(request.POST, request.FILES)
        if form.is_valid():
            try:
                f = request.FILES["file"]
                buf = io.BytesIO()
                for chunk in f.chunks():
                    buf.write(chunk)
                buf.seek(0)
                data = json.load(buf)
                out = io.StringIO()
                workdir = Path(".").absolute()
                with disable_concurrency():
                    kwargs = {
                        "dir": workdir,
                        "prefix": "~IMPORT",
                        "suffix": ".json",
                        "delete": False,
                    }
                    with tempfile.NamedTemporaryFile(**kwargs) as fdst:
                        fdst.write(json.dumps(data).encode())
                    fixture = (workdir / fdst.name).absolute()
                    try:
                        call_command("loaddata", fixture, stdout=out, verbosity=3)
                        out.write("------\n")
                        out.seek(0)
                        context["out"] = out.readlines()
                    finally:
                        fixture.unlink()
            except Exception as e:
                messages.add_message(request, messages.ERROR, f"{e.__class__.__name__}: {e} {out.getvalue()}")

        else:
            context["form"] = form
    else:
        form = ImportForm()
        context["form"] = form
    return render(request, "admin/panels/loaddata.html", context)


panel_loaddata.verbose_name = "Load Data"


def panel_dumpdata(self, request):
    stdout = io.StringIO()
    context = self.each_context(request)
    context["title"] = "Export Configuration"
    if request.method == "POST":
        frm = ExportForm(request.POST)
        if frm.is_valid():
            apps = frm.cleaned_data["apps"]
            call_command(
                "dumpdata",
                *apps,
                stdout=stdout,
                exclude=["registration.Record"],
                use_natural_foreign_keys=True,
                use_natural_primary_keys=True,
            )
            return JsonResponse(
                json.loads(stdout.getvalue()),
                safe=False,
                headers={"Content-Disposition": f"attachment; filename=smart-{VERSION}.json"},
            )
    else:
        frm = ExportForm()
    context["form"] = frm
    return render(request, "admin/panels/dumpdata.html", context)


panel_dumpdata.verbose_name = "Dump Data"


def save_expression(request):
    response = {}
    form = SQLForm(request.POST)
    if form.is_valid():
        name = request.POST["name"]
        profile: UserProfile = request.user.profile
        sql_stms = profile.custom_fields.get("sql_stm", {})
        if len(sql_stms) < 5:
            sql_stms[name] = form.cleaned_data["command"]
            profile.custom_fields["sql_stm"] = sql_stms
            profile.save()

        response = {"message": "Saved"}
    else:
        response = {"error": form.errors}
    return JsonResponse(response)


def panel_sql(self, request, extra_context=None):
    if not request.user.is_superuser:
        raise PermissionDenied
    context = self.each_context(request)
    context["buttons"] = QUICK_SQL
    if request.method == "POST":
        if request.GET.get("op", "") == "save":
            return save_expression(request)

        form = SQLForm(request.POST)
        response = {"result": [], "error": None, "stm": ""}
        if form.is_valid():
            try:
                cmd = form.cleaned_data["command"]
                # stm = urllib.parse.unquote(base64.b64decode(cmd).decode())
                response["stm"] = sqlparse.format(cmd)
                if is_root(request):
                    conn = connections[DEFAULT_DB_ALIAS]
                else:
                    conn = connections["read_only"]
                cursor = conn.cursor()
                cursor.execute(cmd)
                if cursor.pgresult_ptr is not None:
                    response["result"] = cursor.fetchall()
                else:
                    response["result"] = ["Success"]
            except Exception as e:
                response["error"] = str(e)
        else:
            response["error"] = str(form.errors)
        return JsonResponse(response)
    else:
        form = SQLForm()
    context["form"] = form
    return render(request, "admin/panels/sql.html", context)
