import io
import json
import tempfile
from pathlib import Path

from admin_extra_buttons.decorators import button
from admin_extra_buttons.mixins import ExtraButtonsMixin
from concurrency.api import disable_concurrency
from django.contrib import messages
from django.core.management import call_command
from django.http import JsonResponse

from aurora.core.utils import render

from .forms import ImportForm


class LoadDumpMixin(ExtraButtonsMixin):
    @button(label="loaddata")
    def loaddata(self, request):
        opts = self.model._meta
        ctx = self.get_common_context(
            request,
            media=self.media,
            title="Import",
        )
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
                            "prefix": f"~IMPORT-{opts.model_name}",
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
                            ctx["out"] = out.readlines()
                        finally:
                            fixture.unlink()
                except Exception as e:
                    self.message_user(
                        request,
                        f"{e.__class__.__name__}: {e} {out.getvalue()}",
                        messages.ERROR,
                    )
            else:
                ctx["form"] = form
        else:
            form = ImportForm()
            ctx["form"] = form
        return render(request, "admin/registration/registration/import.html", ctx)

    @button()
    def dumpdata(self, request):
        opts = self.model._meta
        stdout = io.StringIO()
        call_command(
            "dumpdata",
            f"{opts.app_label}.{opts.model_name}",
            stdout=stdout,
            use_natural_foreign_keys=True,
            use_natural_primary_keys=True,
        )
        return JsonResponse(
            json.loads(stdout.getvalue()),
            safe=False,
            headers={"Content-Disposition": f"attachment; filename={opts.model_name}.json"},
        )
