from pathlib import Path

import pytest

from brainglobe_stitch.big_stitcher_bridge import run_big_stitcher


def mock_run_capturing_macro(mocker):
    """
    Mock subprocess.run, recording the contents of the temporary macro
    before run_big_stitcher deletes it.
    """
    captured = {}

    def fake_run(command, **kwargs):
        captured["macro"] = Path(command[-1]).read_text()
        return mocker.Mock()

    mock_subprocess_run = mocker.patch(
        "brainglobe_stitch.big_stitcher_bridge.subprocess.run",
        side_effect=fake_run,
    )
    return mock_subprocess_run, captured


def check_call(mock_subprocess_run, captured, expected_imagej_path, args):
    command = mock_subprocess_run.call_args.args[0]
    assert command[:-1] == [
        str(expected_imagej_path),
        "--ij2",
        "--headless",
        "-macro",
    ]
    assert command[-1].endswith(".ijm")
    # The temporary macro is removed after running
    assert not Path(command[-1]).exists()
    assert mock_subprocess_run.call_args.kwargs == dict(
        capture_output=True, text=True, check=True
    )

    expected_line = (
        "args = newArray(" + ", ".join(f'"{arg}"' for arg in args) + ");"
    )
    lines = captured["macro"].splitlines()
    assert lines[0] == expected_line
    assert "getArgument" not in captured["macro"]
    assert lines[1] == "xmlPath = args[0];"


def test_run_big_stitcher_defaults(mocker, test_constants):
    """
    Test the run_big_stitcher function with default parameters. Mocks
    the subprocess.run function to check the command and the values
    written into the macro, and to prevent the actual command from running.
    """
    mock_subprocess_run, captured = mock_run_capturing_macro(mocker)

    imagej_path = test_constants["MOCK_IMAGEJ_PATH"]
    xml_path = test_constants["MOCK_XML_PATH"]
    tile_config_path = test_constants["MOCK_TILE_CONFIG_PATH"]

    run_big_stitcher(imagej_path, xml_path, tile_config_path)

    check_call(
        mock_subprocess_run,
        captured,
        test_constants["MOCK_IMAGEJ_EXEC_PATH"],
        [xml_path, tile_config_path, 0, 488, 4, 4, 1],
    )


@pytest.mark.parametrize(
    "all_channels, selected_channel, downsample_x, downsample_y, downsample_z",
    [
        (False, 488, 4, 4, 4),
        (True, 488, 4, 4, 4),
        (False, 488, 4, 8, 16),
        (True, 576, 4, 8, 16),
    ],
)
def test_run_big_stitcher(
    mocker,
    all_channels,
    selected_channel,
    downsample_x,
    downsample_y,
    downsample_z,
    test_constants,
):
    """
    Test the run_big_stitcher function with custom parameters. Mocks
    the subprocess.run function to check the command and the values
    written into the macro, and to prevent the actual command from running.
    """
    mock_subprocess_run, captured = mock_run_capturing_macro(mocker)

    imagej_path = test_constants["MOCK_IMAGEJ_PATH"]
    xml_path = test_constants["MOCK_XML_PATH"]
    tile_config_path = test_constants["MOCK_TILE_CONFIG_PATH"]

    run_big_stitcher(
        imagej_path,
        xml_path,
        tile_config_path,
        all_channels=all_channels,
        selected_channel=selected_channel,
        downsample_x=downsample_x,
        downsample_y=downsample_y,
        downsample_z=downsample_z,
    )

    check_call(
        mock_subprocess_run,
        captured,
        test_constants["MOCK_IMAGEJ_EXEC_PATH"],
        [
            xml_path,
            tile_config_path,
            int(all_channels),
            selected_channel,
            downsample_x,
            downsample_y,
            downsample_z,
        ],
    )


def test_run_big_stitcher_path_with_spaces(mocker, test_constants, tmp_path):
    """
    Paths containing spaces are passed to the macro intact.
    """
    mock_subprocess_run, captured = mock_run_capturing_macro(mocker)

    xml_path = tmp_path / "mouse 1" / "test_bdv.xml"
    tile_config_path = tmp_path / "mouse 1" / "test_tile_config.txt"

    run_big_stitcher(
        test_constants["MOCK_IMAGEJ_PATH"], xml_path, tile_config_path
    )

    assert f'"{xml_path}", "{tile_config_path}"' in captured["macro"]
