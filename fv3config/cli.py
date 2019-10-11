# -*- coding: utf-8 -*-

"""Console script for fv3config."""
import sys
import click


@click.command()
def main(args=None):
    """Console script for fv3config."""
    click.echo("Replace this message by putting your code into "
               "fv3config.cli.main")
    click.echo("See click documentation at https://click.palletsprojects.com/")
    return 0


if __name__ == "__main__":
    sys.exit(main())  # pragma: no cover
