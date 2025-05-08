import click


@click.command()
@click.version_option(package_name="Aurora", prog_name="Aurora", message="%(version)s")
def cli() -> None:
    pass
