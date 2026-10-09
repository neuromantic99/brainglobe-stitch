"""
Stitch and fuse every mesoSPIM acquisition under an umbrella folder.

Any subfolder (at any depth) containing a "*bdv.h5" file is treated as a
mesoSPIM acquisition. Folders that already contain OUTPUT_NAME are skipped,
so the script can be re-run safely after adding new data or after a failure.

Edit the constants below, then run:
    python examples/batch_stitch.py
"""

import traceback
from pathlib import Path

from brainglobe_stitch.image_mosaic import ImageMosaic

UMBRELLA_FOLDER = Path("/Volumes/MarcBusche/James/Mesospim")
assert (
    UMBRELLA_FOLDER.exists()
), f"Umbrella folder {UMBRELLA_FOLDER} does not exist"

FIJI_PATH = Path("/Applications/Fiji.app")
OUTPUT_NAME = "stitched.h5"

# Channel used for stitching, must match a name in ImageMosaic.channel_names
# (e.g. "488 nm"). An empty string stitches on all channels.
STITCH_CHANNEL = "638 nm"
# Pyramid level BigStitcher computes shifts at (the napari widget uses 2)
STITCH_RESOLUTION_LEVEL = 2

NORMALISE_INTENSITY = True
NORMALISE_INTENSITY_PERCENTILE = 80
INTERPOLATE_OVERLAPS = True


def subfolders(folder: Path) -> list[Path]:
    return [subfolder for subfolder in folder.glob("*/") if subfolder.is_dir()]


def find_folders_to_stitch(umbrella_folder: Path) -> list[Path]:
    dates = [
        date
        for date in subfolders(umbrella_folder)
        if date.name.startswith("20")
    ]

    to_stitch = []

    for date in dates:
        mice = subfolders(date)
        for mouse in mice:
            acquisitions = subfolders(mouse)
            for acquisition in acquisitions:
                if not any(acquisition.glob("*bdv.h5")):
                    continue

                folder = acquisition

                output_path = folder / OUTPUT_NAME
                if output_path.exists():
                    if not output_path.with_suffix(".xml").exists():
                        # The xml is written after fusing, so a missing xml means
                        # a previous run probably died part way through
                        print(
                            f"WARNING: {output_path} exists without its .xml, it may "
                            "be incomplete. Delete it to re-stitch this folder."
                        )
                    continue
                to_stitch.append(folder)
    return to_stitch


def stitch_folder(folder: Path) -> None:
    mosaic = ImageMosaic(folder)
    try:
        mosaic.stitch(
            FIJI_PATH,
            resolution_level=STITCH_RESOLUTION_LEVEL,
            selected_channel=STITCH_CHANNEL,
        )
        mosaic.fuse(
            folder / OUTPUT_NAME,
            normalise_intensity=NORMALISE_INTENSITY,
            normalise_intensity_percentile=NORMALISE_INTENSITY_PERCENTILE,
            interpolate=INTERPOLATE_OVERLAPS,
        )
    finally:
        if mosaic.h5_file:
            mosaic.h5_file.close()
            mosaic.h5_file = None


def main() -> None:
    folders = find_folders_to_stitch(UMBRELLA_FOLDER)
    print(f"Found {len(folders)} folder(s) to stitch")

    failed = []
    for i, folder in enumerate(folders, start=1):
        print(f"\n[{i}/{len(folders)}] Stitching {folder}")
        try:
            stitch_folder(folder)
        except Exception:
            traceback.print_exc()
            failed.append(folder)

    print(f"\nDone: {len(folders) - len(failed)}/{len(folders)} succeeded")
    for folder in failed:
        print(f"FAILED: {folder}")


if __name__ == "__main__":
    main()
