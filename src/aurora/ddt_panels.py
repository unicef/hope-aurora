from typing import TYPE_CHECKING

from debug_toolbar.panels import Panel
from django.template import Context, Template
from django.utils.translation import gettext_lazy as _

from aurora.state import state

if TYPE_CHECKING:
    from django.utils.functional import _StrPromise


TEMPLATE = """
<h2>{{state}}</h2>
<table>
<tr><th>request</th><td>{{state.request}}</td></tr>
{% for k,v in state.data.items %}
<tr><th>{{k}}</th><td>{{v}}</td></tr>
{% endfor %}
</table>

<h2>Info</h2>
<table>
<tr><th>User</th><td>{{state.user}}</td></tr>
<tr><th>  staff</th><td>{{state.user.is_staff}}</td></tr>
<tr><th>  superuser</th><td>{{state.user.is_superuser}}</td></tr>
</table>

"""
TEMPLATE2 = """
<pre>
{{stdout}}
</pre>
"""


class StatePanel(Panel):
    name = "state"
    has_content = True

    def nav_title(self) -> "_StrPromise":
        return _("State")

    @property
    def enabled(self) -> bool:
        return True

    def title(self) -> "_StrPromise":
        return _("State Panel")

    def url(self) -> str:
        return ""

    @property
    def content(self) -> str:
        context = Context(
            {
                "state": state,
            }
        )
        template = Template(TEMPLATE)
        return template.render(context)
