import base64

from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.files.utils import FileProxyMixin

from aurora.core.utils import apply_nested, merge_data

marker = object()


def clean_dict(d, filter_func):
    ret = {}
    if filter_func(d):
        return ret
    if isinstance(d, dict):
        for key, value in list(d.items()):
            if filter_func(value):
                del d[key]
                continue
            elif isinstance(value, dict):
                new_val = clean_dict(value, filter_func)
            elif isinstance(value, list) and value:
                if isinstance(value[0], dict):
                    new_val = [clean_dict(e, filter_func) for e in value]
                else:
                    new_val = [e for e in value if not filter_func(e)]
            else:
                new_val = value
            if new_val:
                ret[key] = new_val or None
    return ret


class Router:
    def compress(self, fields, files):
        ff = apply_nested(files, lambda v, k: SimpleUploadedFile(k, v if isinstance(v, bytes) else v.encode()))
        return merge_data(fields, ff)

    def decompress(self, data):
        def files_exclude(v, k):
            if isinstance(v, FileProxyMixin):
                return "::file::"
            return v

        def files_keep(v, k):
            if isinstance(v, FileProxyMixin):
                return base64.b64encode(v.read())
            return marker

        fields = {field_name: apply_nested(field, files_exclude) for field_name, field in data.items()}
        files = {field_name: apply_nested(field, files_keep) for field_name, field in data.items()}

        fields = clean_dict(fields, lambda x: x == "::file::")
        files = clean_dict(files, lambda x: x is marker)
        return fields, files


router = Router()
