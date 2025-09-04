import click
from cloup import Context, HelpFormatter, Style, HelpTheme
import cloup

from abstract_algebra.applications.coding_theory.cksum import Checksum


CONTEXT_SETTINGS = Context.settings(
    align_option_groups=True,
    align_sections=True,
    show_constraints=True,
    show_subcommand_aliases=True,
    formatter_settings=HelpFormatter.settings(
        max_width=100,
        col1_max_width=40,
        col2_min_width=60,
        indent_increment=3,
        col_spacing=3,
        theme=HelpTheme(
            invoked_command=Style(fg='bright_yellow'),
            heading=Style(fg='bright_white', bold=True),
            constraint=Style(fg='magenta'),
            col1=Style(fg='bright_yellow')
        )
    )
)


@cloup.group()
def cli() -> None:
    pass


@cli.command("checksum", aliases=["cksum"])
@cloup.argument("data", type=str, required=True)
def cli_checksum(data: str) -> None:
    checksum = Checksum.from_bytes(data.encode("utf-8"))
    click.secho(f"{checksum} {len(data)}")
    
    
def run() -> None:
    try:
        cli()
    except Exception as e:
        raise e
    
    
if __name__ == "__main__":
    run()