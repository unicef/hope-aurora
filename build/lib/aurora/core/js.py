import json
import logging
from json import JSONDecodeError
from pathlib import Path
from typing import Any

from django.core.exceptions import ValidationError
from django.utils.translation import gettext as _
from dukpy import JSRuntimeError

from aurora.core.utils import JSONEncoder
from aurora.exceptions import JSEngineError

logger = logging.getLogger(__name__)


class JsValidator:
    CONSOLE = """
    console = {log: function(d) {}};
    """
    LIB = (Path(__file__).parent / "static" / "smart_validation.min.js").read_text()

    def __init__(self, code):
        self.code = code

    def jspickle(self, value):
        return json.dumps(value, cls=JSONEncoder, skip_files=True)

    def run(self, field_value: Any) -> Any: ...

    def validate(self, field_value: Any) -> bool:
        try:
            result = self.run(field_value)
            try:
                ret = json.loads(result)
            except (JSONDecodeError, TypeError):
                ret = result

            if (ret is None) or isinstance(ret, bool) and not ret:
                raise ValidationError(_("Please insert a valid value"))
            if isinstance(ret, str):
                raise ValidationError(_(ret))
            if isinstance(ret, list | tuple):
                errors = [_(v) for v in ret]
                raise ValidationError(errors)
            if isinstance(ret, dict):
                errors = {k: _(v) for (k, v) in ret.items()}
                raise ValidationError(errors)
        except Exception as e:
            logger.exception(e)
            raise
        return True


class DukPYValidator(JsValidator):
    def run(self, field_value: str) -> str:
        import dukpy

        pickled = self.jspickle(field_value or "")
        code = f"""{self.LIB};
var value = {pickled};
{self.code}
"""
        try:
            return dukpy.evaljs(code)
        except JSRuntimeError as e:
            logger.exception(e)
            raise JSEngineError() from e
