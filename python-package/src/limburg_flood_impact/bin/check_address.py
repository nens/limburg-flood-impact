import argparse
from pathlib import Path
import sys

from ..check_address import check_building_have_address


def main():

    parser = argparse.ArgumentParser(prog='CheckAddress',
                                     description='Determines if the building has address.',
                                     epilog='')

    parser.add_argument(
        '-b',
        '--buildings',
        type=lambda p: Path(p).absolute(),
        help="Path to the file with buildings.",
        required=True
    )

    parser.add_argument(
        '-a',
        '--addresses',
        type=lambda p: Path(p).absolute(),
        help="Path to the file with addresses.",
        required=True
    )

    args = parser.parse_args()

    buildings_path: Path = args.buildings
    address_path: Path = args.addresses

    if not buildings_path.exists():
        print("File {} does not exist.".format(buildings_path.absolute().as_posix()))
        return

    if not address_path.exists():
        print("File {} does not exist.".format(address_path.absolute().as_posix()))
        return

    check_building_have_address(buildings_path, address_path)


if __name__ == "__main__":

    sys.exit(main())
