import logging
from typing import TYPE_CHECKING

import sqlparse
from django.core.exceptions import PermissionDenied
from django.db import DEFAULT_DB_ALIAS, connections
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render
from smart_admin.site import SmartAdminSite

from ..core.utils import is_root
from .forms import SQLForm

if TYPE_CHECKING:
    from django.forms.utils import ErrorDict

    from ..security.models import UserProfile
    from ..types.http import AuthHttpRequest

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


def save_expression(request: "AuthHttpRequest") -> JsonResponse:
    response: dict[str, str | ErrorDict]
    form = SQLForm(request.POST)
    if form.is_valid():
        name = request.POST["name"]
        profile: UserProfile = request.user.profile
        sql_stms = profile.custom_fields.get("sql_stm", [])
        if len(sql_stms) >= 5:
            sql_stms = sql_stms[1:]
        sql_stms.append((name, form.cleaned_data["command"]))
        profile.custom_fields["sql_stm"] = sql_stms
        profile.save()

        response = {"message": "Saved"}
    else:
        response = {"error": form.errors}
    return JsonResponse(response)


def panel_sql(self: SmartAdminSite, request: "AuthHttpRequest", extra_context: dict | None = None) -> HttpResponse:
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
            except Exception as e:  # noqa: BLE001
                response["error"] = str(e)
        else:
            response["error"] = str(form.errors)
        return JsonResponse(response)
    form = SQLForm()
    context["form"] = form
    return render(request, "admin/panels/sql.html", context)
