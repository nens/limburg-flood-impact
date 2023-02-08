import argparse
from pathlib import Path
import sys

from ..test_against_flood_protection_norm import test_against_flood_protection_norm
from .._functions import print_percent


def main():

    parser = argparse.ArgumentParser(prog='TestAgainstFloodProtectionNorm',
                                     description='Test Against Flood Protection Norm.',
                                     epilog='')

    parser.add_argument(
        '-b',
        '--buildings',
        type=lambda p: Path(p).absolute(),
        help="Path to the file with buildings.",
        required=True
    )

    parser.add_argument(
        '-f',
        '--flood_norm',
        type=lambda p: Path(p).absolute(),
        help="Path to the file with flood areas.",
        required=True
    )

    args = parser.parse_args()

    buildings_path: Path = args.buildings
    flood_norm_path: Path = args.flood_norm

    if not buildings_path.exists():
        print("File {} does not exist.".format(buildings_path.absolute().as_posix()))
        return

    if not flood_norm_path.exists():
        print("File {} does not exist.".format(flood_norm_path.absolute().as_posix()))
        return

    test_against_flood_protection_norm(buildings_path, flood_norm_path, print_percent)


if __name__ == "__main__":

    sys.exit(main())
