"""
Add hreflang response headers as specified by Google

https://support.google.com/webmasters/answer/189077?hl=en
"""

from django.utils.deprecation import MiddlewareMixin

from .functions import get_hreflang_info


def hreflang_headers(response, request=None, path=None):
    """
    Adds hreflang headers to a HttpResponse object

    :param response: the HttpResponse to add headers to
    :param path: the current path for which to add alternate language versions
    :param request: the request, which is used to find path (ignored if path is set directly)
    :return: response is modified and returned
    """
    assert request or path, "hreflang_headers needs the current url, please either provide request or a path"
    links = []
    hreflang_info = get_hreflang_info(path or request.path)
    for lang, url in hreflang_info:
        links.append('<{1}>; rel="alternate"; hreflang="{0}"'.format(lang, url))
    response["Link"] = "{0},".format(response["Link"]) if "Link" in response else ""
    response["Link"] += ",".join(links)
    return response


class AddHreflangToResponse(MiddlewareMixin):
    """
    A middleware that applies hreflang_headers to all responses (adding hreflang headers).
    """

    def process_response(self, request, response):
        return hreflang_headers(response, request=request)
