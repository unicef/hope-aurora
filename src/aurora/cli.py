import click


@click.group()
@click.version_option(package_name="Aurora", prog_name="Aurora", message="%(version)s")
def cli() -> None:
    pass
