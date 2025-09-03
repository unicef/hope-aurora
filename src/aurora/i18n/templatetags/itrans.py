from decimal import Decimal
from typing import Any

from django.template import Context, Library, Node, TemplateSyntaxError, Variable
from django.template.base import FilterExpression, Parser, Token, TokenType, render_value_in_context, token_kwargs
from django.templatetags.static import static
from django.utils import translation
from django.utils.safestring import mark_safe
from django.utils.translation import get_language

from ..engine import translator

register = Library()


class TranslateNode(Node):
    child_nodelists = ()
    noop: bool
    asvar: str | None
    message_context: FilterExpression | None
    filter_expression: FilterExpression

    def __init__(
        self,
        filter_expression: FilterExpression,
        noop: bool,
        asvar: str | None = None,
        message_context: FilterExpression | None = None,
    ) -> None:
        self.noop = noop
        self.asvar = asvar
        self.message_context = message_context
        self.filter_expression = filter_expression
        if isinstance(self.filter_expression.var, str):
            self.filter_expression.var = Variable("'%s'" % self.filter_expression.var)

    def render(self, context: Context) -> str:
        self.filter_expression.var.translate = not self.noop
        if self.message_context:
            self.filter_expression.var.message_context = self.message_context.resolve(context)
        output = self.filter_expression.resolve(context)
        value = render_value_in_context(output, context)
        # Restore percent signs. Percent signs in template text are doubled
        # so they are not interpreted as string format flags.

        current_locale = get_language()
        if self.filter_expression.var.literal:
            msgid = self.filter_expression.var.literal
        else:
            msgid = self.filter_expression.resolve(context)

        value = translator[current_locale][msgid]

        if self.asvar:
            context[self.asvar] = str(value)
            context[f"{self.asvar}_msgid"] = msgid
            return ""
        return str(value)


class BlockTranslateNode(Node):
    extra_context: dict[str, FilterExpression]
    singular: list[Token]
    plural: list[Token]
    countervar: str | None
    counter: FilterExpression | None
    message_context: FilterExpression | None
    trimmed: bool
    asvar: str | None

    def __init__(  # noqa: PLR0913
        self,
        extra_context: dict[str, FilterExpression],
        singular: list[Token],
        plural: list[Token] | None = None,
        countervar: str | None = None,
        counter: FilterExpression | None = None,
        message_context: FilterExpression | None = None,
        trimmed: bool = False,
        asvar: str | None = None,
        tag_name: str = "blocktranslate",
    ) -> None:
        self.extra_context = extra_context
        self.singular = singular
        self.plural = plural
        self.countervar = countervar
        self.counter = counter
        self.message_context = message_context
        self.trimmed = trimmed
        self.asvar = asvar
        self.tag_name = tag_name

    def render_token_list(self, tokens: list[Token]) -> tuple[str, list[str]]:
        result = []
        variables = []
        for token in tokens:
            if token.token_type == TokenType.TEXT:
                result.append(token.contents.replace("%", "%%"))
            elif token.token_type == TokenType.VAR:
                result.append("%%(%s)s" % token.contents)
                variables.append(token.contents)
        msg = "".join(result)
        if self.trimmed:
            msg = translation.trim_whitespace(msg)
        return msg, variables

    def render(self, context: Context, nested: bool = False) -> str:  # noqa: C901
        if self.message_context:
            message_context = self.message_context.resolve(context)
        else:
            message_context = None
        # Update() works like a push(), so corresponding context.pop() is at
        # the end of function
        current_locale = get_language()

        context.update({var: val.resolve(context) for var, val in self.extra_context.items()})
        singular, variables = self.render_token_list(self.singular)
        if self.plural and self.countervar and self.counter:
            count = int(self.counter.resolve(context))
            if not isinstance(count, Decimal | float | int):
                raise TemplateSyntaxError("%r argument to %r tag must be a number." % (self.countervar, self.tag_name))
            context[self.countervar] = count
            plural, plural_vars = self.render_token_list(self.plural)
            if message_context:
                result = translation.npgettext(message_context, singular, plural, count)
            else:
                result = translator[current_locale].ngettext(singular, plural, count)
            variables.extend(plural_vars)
        elif message_context:
            result = translator[current_locale][singular]
        else:
            result = translator[current_locale][singular]

        default_value = context.template.engine.string_if_invalid

        def render_value(key: str) -> str:
            if key in context:
                val = context[key]
            else:
                val = default_value % key if "%s" in default_value else default_value
            return render_value_in_context(val, context)

        data = {v: translator[current_locale][render_value(v)] for v in variables}
        context.pop()
        try:
            result = result % data
        except (KeyError, ValueError):
            if nested:
                # Either string is malformed, or it's a bug
                raise TemplateSyntaxError(
                    "%r is unable to format string returned by gettext: %r using %r" % (self.tag_name, result, data)
                ) from None
            with translation.override(None):
                result = self.render(context, nested=True)
        if self.asvar:
            context[self.asvar] = str(result)
            return ""
        return str(result)


@register.tag("translate")
@register.tag("trans")
def do_translate(parser: Parser, token: Token) -> TranslateNode:
    bits = token.split_contents()
    if len(bits) < 2:
        raise TemplateSyntaxError("'%s' takes at least one argument" % bits[0])
    message_string = parser.compile_filter(bits[1] or "")
    remaining = bits[2:]

    noop = False
    asvar = None
    message_context = None
    seen = set()
    invalid_context = {"as", "noop"}

    while remaining:
        option = remaining.pop(0)
        if option in seen:
            raise TemplateSyntaxError(
                "The '%s' option was specified more than once." % option,
            )
        if option == "noop":
            noop = True
        elif option == "context":
            try:
                value = remaining.pop(0)
            except IndexError:
                raise TemplateSyntaxError(
                    "No argument provided to the '%s' tag for the context option." % bits[0]
                ) from None
            if value in invalid_context:
                raise TemplateSyntaxError(
                    "Invalid argument '%s' provided to the '%s' tag for the context option" % (value, bits[0]),
                )
            message_context = parser.compile_filter(value)
        elif option == "as":
            try:
                value = remaining.pop(0)
            except IndexError:
                raise TemplateSyntaxError("No argument provided to the '%s' tag for the as option." % bits[0]) from None
            asvar = value
        else:
            raise TemplateSyntaxError(
                "Unknown argument for '%s' tag: '%s'. The only options "
                "available are 'noop', 'context' \"xxx\", and 'as VAR'."
                % (
                    bits[0],
                    option,
                )
            )
        seen.add(option)

    return TranslateNode(message_string, noop, asvar, message_context)


@register.tag("blocktranslate")
@register.tag("blocktrans")
def do_block_translate(parser: Parser, token: Token) -> BlockTranslateNode:  # noqa
    """
    Translate a block of text with parameters.

    Usage::

        {% blocktranslate with bar=foo|filter boo=baz|filter %}
        This is {{ bar }} and {{ boo }}.
        {% endblocktranslate %}

    Additionally, this supports pluralization::

        {% blocktranslate count count=var|length %}
        There is {{ count }} object.
        {% plural %}
        There are {{ count }} objects.
        {% endblocktranslate %}

    This is much like ngettext, only in template syntax.

    The "var as value" legacy format is still supported::

        {% blocktranslate with foo|filter as bar and baz|filter as boo %}
        {% blocktranslate count var|length as count %}

    The translated string can be stored in a variable using `asvar`::

        {% blocktranslate with bar=foo|filter boo=baz|filter asvar var %}
        This is {{ bar }} and {{ boo }}.
        {% endblocktranslate %}
        {{ var }}

    Contextual translations are supported::

        {% blocktranslate with bar=foo|filter context "greeting" %}
            This is {{ bar }}.
        {% endblocktranslate %}

    This is equivalent to calling pgettext/npgettext instead of
    (u)gettext/(u)ngettext.
    """
    bits = token.split_contents()

    options = {}
    remaining_bits = bits[1:]
    asvar: str | None = None
    value: str | dict | None | FilterExpression | bool
    while remaining_bits:
        option = remaining_bits.pop(0)
        if option in options:
            raise TemplateSyntaxError("The %r option was specified more than once." % option)
        if option == "with":
            value = token_kwargs(remaining_bits, parser, support_legacy=True)
            if not value:
                raise TemplateSyntaxError('"with" in %r tag needs at least one keyword argument.' % bits[0])
        elif option == "count":
            value = token_kwargs(remaining_bits, parser, support_legacy=True)
            if len(value) != 1:
                raise TemplateSyntaxError('"count" in %r tag expected exactly one keyword argument.' % bits[0])
        elif option == "context":
            try:
                value = remaining_bits.pop(0)
                value: FilterExpression | None = parser.compile_filter(value)  # type: ignore[no-redef]
            except Exception:  # noqa: BLE001
                raise TemplateSyntaxError('"context" in %r tag expected exactly one argument.' % bits[0]) from None
        elif option == "trimmed":
            value = True
        elif option == "asvar":
            try:
                value = remaining_bits.pop(0)
            except IndexError:
                raise TemplateSyntaxError(
                    "No argument provided to the '%s' tag for the asvar option." % bits[0]
                ) from None
            asvar = value
        else:
            raise TemplateSyntaxError("Unknown argument for %r tag: %r." % (bits[0], option))
        options[option] = value

    if "count" in options:
        countervar, counter = next(iter(options["count"].items()))  # type: ignore[union-attr]
    else:
        countervar, counter = None, None
    message_context: FilterExpression = options.get("context")  # type: ignore[assignment]
    extra_context: dict[str, FilterExpression] = options.get("with", {})  # type: ignore[assignment]

    trimmed: bool = options.get("trimmed", False)  # type: ignore[assignment]

    singular = []
    plural = []
    while parser.tokens:
        token = parser.next_token()
        if token.token_type in (TokenType.VAR, TokenType.TEXT):
            singular.append(token)
        else:
            break
    if countervar and counter:
        if token.contents.strip() != "plural":
            raise TemplateSyntaxError("%r doesn't allow other block tags inside it" % bits[0])
        while parser.tokens:
            token = parser.next_token()
            if token.token_type in (TokenType.VAR, TokenType.TEXT):
                plural.append(token)
            else:
                break
    end_tag_name = "end%s" % bits[0]
    if token.contents.strip() != end_tag_name:
        raise TemplateSyntaxError("%r doesn't allow other block tags (seen %r) inside it" % (bits[0], token.contents))

    return BlockTranslateNode(
        extra_context,
        singular,
        plural,
        countervar,
        counter,
        message_context,
        trimmed=trimmed,
        asvar=asvar,
        tag_name=bits[0],
    )


@register.filter()
def md5(value: str, lang: str) -> str:
    from aurora.i18n.models import Message

    return Message.get_md5(value, lang)


@register.filter()
def msgcode(value: str) -> str:
    from aurora.i18n.models import Message

    return Message.get_md5(str(value))


@register.filter()
def strip(value: str) -> str:
    return str(value).strip()


@register.filter()
def bool_icon(value: Any) -> str:
    if bool(value):
        img = static("admin/img/icon-yes.svg")
    else:
        img = static("admin/img/icon-no.svg")
    return mark_safe(f'<img src="{img}" alt="{str(bool(value))}">')  # noqa: S308
