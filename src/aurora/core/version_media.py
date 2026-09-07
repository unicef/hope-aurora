from itertools import chain
from typing import Any, Iterable

from django import forms
from django.forms import Media
from django.utils.html import format_html, html_safe
from django.utils.safestring import SafeString

import aurora


@html_safe
class VersionMedia(forms.Media):
    _css_lists: list[str]
    _js_lists: list[str]
    _css: dict

    def __str__(self) -> str:
        return self.render()

    def render_css(self, *, attrs: Any | None = None) -> Iterable[SafeString]:
        # To keep rendering order consistent, we can't just iterate over items().
        # We need to sort the keys, and iterate over the sorted list.
        media = sorted(self._css)
        version = aurora.__version__
        return chain.from_iterable(
            [
                format_html(
                    '<link href="{}?{}" type="text/css" media="{}" rel="stylesheet">',
                    self.absolute_path(path),
                    version,
                    medium,
                )
                for path in self._css[medium]
            ]
            for medium in media
        )

    def __add__(self, other: Media) -> Media:
        combined = VersionMedia()
        combined._css_lists = self._css_lists[:]
        combined._js_lists = self._js_lists[:]
        for item in other._css_lists:  # type: ignore[attr-defined]
            if item and item not in self._css_lists:
                combined._css_lists.append(item)
        for item in other._js_lists:  # type: ignore[attr-defined]
            if item and item not in self._js_lists:
                combined._js_lists.append(item)
        return combined
