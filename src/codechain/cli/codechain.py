from pathlib import Path
from typing import Literal
import click
from cloup import Context, HelpFormatter, Style, HelpTheme
import cloup

from codechain.core.checksum.crc import CRC
from codechain.core.factories import CodecPipelineFactory
from codechain.core.models import CodecPipelineSpec
from codechain.core.pipeline import CodecPipeline
from codechain.utils.serialization import SerUtils
from codechain.utils.io import StreamIO


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
            invoked_command=Style(fg="bright_yellow"),
            heading=Style(fg="bright_white", bold=True),
            constraint=Style(fg="magenta"),
            col1=Style(fg="bright_yellow"),
        ),
    ),
)


def _create_codec_pipeline(pipeline_file: str) -> CodecPipeline:
    unmarshalled = SerUtils.from_file(Path(pipeline_file).resolve(), ["yaml", "json"])
    spec = CodecPipelineSpec.model_validate(unmarshalled)
    return CodecPipelineFactory.build(spec)


@cloup.group(
    context_settings=CONTEXT_SETTINGS,
    help="Codechain CLI — encode, decode and checksum data using codec pipelines.",
)
def codechain() -> None:
    pass


@codechain.command(
    "checksum",
    aliases=["cksum"],
    help="Compute CRC checksum of input stream (read from stdin).",
)
@cloup.option(
    "-n",
    "--size",
    "size",
    type=click.Choice([8, 16, 32]),
    default=32,
    show_default=True,
    help="CRC size in bits (8, 16, or 32).",
)
def codechain_checksum(size: int) -> None:
    """Read bytes from stdin and output CRC checksum + number of bytes read."""
    try:
        stream = StreamIO()
        cksum = CRC.checksum(stream.read_bytes(), size)
        click.secho(f"{cksum} {stream.read_count()}")
    except Exception as e:
        click.secho(f"ERROR: {e}", err=True, fg="yellow")


@codechain.command(
    "encode",
    aliases=["e", "enc"],
    help="Encode input using the codec pipeline defined in a pipeline file.",
)
@cloup.argument("input", type=str, required=True, help="Input data to encode.")
@cloup.option(
    "-enc",
    "--encoding",
    "input_encoding",
    type=click.Choice(["hex", "utf-8"]),
    default="utf-8",
    required=True,
    help="Encoding of the input string (utf-8 text or hex).",
)
@cloup.option(
    "-f",
    "--pipeline-file",
    "pipeline_file",
    type=click.Path(exists=True, dir_okay=False, resolve_path=True),
    required=True,
    default="pipeline.yaml",
    show_default=True,
    help="Path to pipeline spec file (YAML or JSON).",
)
def codechain_encode(
    input: str, input_encoding: Literal["hex", "utf-8"], pipeline_file: str
) -> None:
    """Encode input data through the configured pipeline."""
    try:
        pipeline = _create_codec_pipeline(pipeline_file)
        data = input.encode("utf-8") if input_encoding == "utf-8" else bytes.fromhex(input)
        encoded = pipeline.encode(data)
        click.secho(f"{encoded.hex()} {len(encoded)}")
    except Exception as e:
        click.secho(f"ERROR: {e}", err=True, fg="yellow")


@codechain.command(
    "decode",
    aliases=["d", "dec"],
    help="Decode input using the codec pipeline defined in a pipeline file.",
)
@cloup.argument("input", type=str, required=True, help="Input data to decode (hex string).")
@cloup.option(
    "-enc",
    "--encoding",
    "output_encoding",
    type=click.Choice(["hex", "utf-8"]),
    default="utf-8",
    required=True,
    help="Encoding for decoded output (utf-8 text or hex).",
)
@cloup.option(
    "-f",
    "--pipeline-file",
    "pipeline_file",
    type=click.Path(exists=True, dir_okay=False, resolve_path=True),
    required=True,
    default="pipeline.yaml",
    show_default=True,
    help="Path to pipeline spec file (YAML or JSON).",
)
def codechain_decode(
    input: str, output_encoding: Literal["hex", "utf-8"], pipeline_file: str
) -> None:
    """Decode input data through the configured pipeline."""
    try:
        pipeline = _create_codec_pipeline(pipeline_file)
        decoded = pipeline.decode(bytes.fromhex(input))
        out = decoded.decode("utf-8") if output_encoding == "utf-8" else decoded.hex()
        click.secho(f"{out} {len(decoded)}")
    except Exception as e:
        click.secho(f"ERROR: {e}", err=True, fg="yellow")


def run() -> None:
    try:
        codechain()
    except Exception as e:
        raise e


if __name__ == "__main__":
    run()
