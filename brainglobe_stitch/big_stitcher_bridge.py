import subprocess
import tempfile
from pathlib import Path
from platform import system


def run_big_stitcher(
    imagej_path: Path,
    xml_path: Path,
    tile_config_path: Path,
    all_channels: bool = False,
    selected_channel: int = 488,
    downsample_x: int = 4,
    downsample_y: int = 4,
    downsample_z: int = 1,
) -> subprocess.CompletedProcess:
    """
    Run the BigStitcher ImageJ macro. Output is captured and returned as part
    of the subprocess.CompletedProcess.

    Parameters
    ----------
    imagej_path : Path
        The path to the ImageJ executable.
    xml_path : Path
        The path to the BigDataViewer XML file.
    tile_config_path : Path
        The path to the BigStitcher tile configuration file.
    all_channels : bool, optional
        Whether to stitch based on all channels (default False).
    selected_channel : int, optional
        The channel on which to base the stitching (default 488).
    downsample_x : int, optional
        The downsample factor in the x-dimension for the stitching (default 4).
    downsample_y : int, optional
        The downsample factor in the y-dimension for the stitching (default 4).
    downsample_z : int, optional
        The downsample factor in the z-dimension for the stitching (default 1).

    Returns
    -------
    subprocess.CompletedProcess
        The result of the subprocess run.

    Raises
    ------
    subprocess.CalledProcessError
        If the subprocess returns a non-zero exit status.
    """
    stitch_macro_path = (
        Path(__file__).resolve().parent / "bigstitcher_macro.ijm"
    )

    if system().startswith("Darwin"):
        imagej_path = imagej_path / "Contents/MacOS/ImageJ-macosx"

    # Some Fiji launchers split the -macro argument string on whitespace,
    # so the macro only sees the first value. Write the values directly
    # into a temporary copy of the macro instead of passing them as an
    # argument. This also allows paths containing spaces.
    macro_args = [
        xml_path,
        tile_config_path,
        int(all_channels),
        selected_channel,
        downsample_x,
        downsample_y,
        downsample_z,
    ]
    macro_args_line = (
        "args = newArray("
        + ", ".join(_macro_string(arg) for arg in macro_args)
        + ");"
    )
    macro_body = stitch_macro_path.read_text().split("\n", 2)[2]

    with tempfile.NamedTemporaryFile(
        "w", suffix=".ijm", delete=False
    ) as macro_file:
        macro_file.write(macro_args_line + "\n" + macro_body)
        temp_macro_path = Path(macro_file.name)

    command = [
        str(imagej_path),
        "--ij2",
        "--headless",
        "-macro",
        str(temp_macro_path),
    ]

    try:
        result = subprocess.run(
            command, capture_output=True, text=True, check=True
        )
    finally:
        temp_macro_path.unlink()

    return result


def _macro_string(value) -> str:
    """
    Format a value as an ImageJ macro string literal.
    """
    escaped = str(value).replace("\\", "/").replace('"', '\\"')
    return f'"{escaped}"'
