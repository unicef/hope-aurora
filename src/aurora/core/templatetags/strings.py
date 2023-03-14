from django.template import Library

register = Library()


@register.filter(name="split")
def split(value, key):
    """
    Returns the value turned into a list.
    """
    return value.split(key)


@register.filter
def replace(value, arg):
    """
    Replacing filter
    Use `{{ "aaa"|replace:"a|b" }}`
    """
    if len(arg.split("|")) != 2:
        return value

    what, to = arg.split("|")
    return value.replace(what, to)
