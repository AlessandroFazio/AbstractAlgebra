import click
from cloup import Context, HelpFormatter, Style, HelpTheme
import cloup

from abstract_algebra.applications.coding_theory.cksum import Checksum
from abstract_algebra.applications.coding_theory.reed_solomon import ReedSolomonCodec


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
def abstralg() -> None:
    pass

@abstralg.command("checksum", aliases=["cksum"])
@cloup.argument("data", type=str, required=True)
def abstralg_checksum(data: str) -> None:
    checksum = Checksum.of(data.encode("utf-8"))
    click.secho(f"{checksum} {len(data)}")
    
@abstralg.command("reed-solomon", aliases=["rs"])
@cloup.argument("data", type=str, required=True)
@cloup.option("-r", "--code-rate", "code_rate", type=float, default=0.80, show_default=True)
@cloup.option("-d", "--decode", "decode", type=bool, is_flag=True, default=False, show_default=True)
def abstralg_reed_solomon(data: str, code_rate: float, decode: bool) -> None:
    rs = ReedSolomonCodec.of(code_rate)
    out = None
    if decode:
        out = rs.decode(bytes.fromhex(data))
        click.secho(f"{out.decode('utf-8')} {len(out)}")
    else:
        out = rs.encode(data.encode("utf-8")) 
        click.secho(f"{out.hex()} {len(out)}")
    
def run() -> None:
    try:
        abstralg()
    except Exception as e:
        raise e
    
    
if __name__ == "__main__":
    run()