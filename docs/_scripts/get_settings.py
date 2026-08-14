import mkdocs_gen_files

from aurora.config import env

MD_HEADER = """# Settings

Aurora is configured through environment variables. Every setting below is
optional unless marked otherwise: unset variables fall back to the default
value shown. Values marked as required ("explicit") must be provided in
production.

"""

MD_LINE = """
### {key}
_Default_: `{default_value}`

{help}

"""

DEV_LINE = """
__Suggested value for development__: `{develop_value}`
"""

DYNAMIC_DEFAULTS = {
    "DJANGO_ADMIN_URL": "randomly generated at startup (set it explicitly, e.g. admin/)",
    "FRONT_DOOR_TOKEN": "randomly generated at startup",
}

OUTFILE = "settings.md"
with mkdocs_gen_files.open(OUTFILE, "w") as f:
    f.write(MD_HEADER)
    for entry, cfg in sorted(env.config.items()):
        default_value = cfg["default"]
        if entry in DYNAMIC_DEFAULTS:
            default_value = DYNAMIC_DEFAULTS[entry]
        f.write(
            MD_LINE.format(
                key=entry,
                default_value=default_value,
                help=cfg["help"] or "No description available.",
            )
        )
        develop_value = cfg["develop"]
        if develop_value and not cfg["explicit"] and develop_value != cfg["default"]:
            f.write(
                DEV_LINE.format(
                    key=entry,
                    default_value=default_value,
                    develop_value=develop_value,
                    help=cfg["help"] or "No description available.",
                )
            )
mkdocs_gen_files.set_edit_path(OUTFILE, "get_settings.py")
