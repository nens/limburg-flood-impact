import argparse
import sys
from pathlib import Path

from ..check_address import check_building_have_address
from ..default_field_names import DEFAULT_BUILDING_ID_FIELD
from ..default_field_names import DEFAULT_ADDRESS_BUILDING_ID_FIELD


def main():
    parser = argparse.ArgumentParser(
        prog="CheckAddress",
        description="Determines if the building has address.",
        epilog="",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )

    parser.add_argument(
        "-b",
        "--buildings",
        type=lambda p: Path(p).absolute(),
        help="Path to the file with buildings.",
        required=True,
    )

    parser.add_argument(
        "-a",
        "--addresses",
        type=lambda p: Path(p).absolute(),
        help="Path to the file with addresses.",
        required=True,
    )

    parser.add_argument(
        "--building-id-field",
        type=str,
        help="Name of the building id field in the buildings file.",
        default=DEFAULT_BUILDING_ID_FIELD,
    )

    parser.add_argument(
        "--address-building-id-field",
        type=str,
        help="Name of the building id field in the addresses file.",
        default=DEFAULT_ADDRESS_BUILDING_ID_FIELD,
    )

    args = parser.parse_args()

    buildings_path: Path = args.buildings
    address_path: Path = args.addresses
    building_id_field = args.building_id_field
    address_building_id_field = args.address_building_id_field

    if not buildings_path.exists():
        print("File {} does not exist.".format(buildings_path.absolute().as_posix()))
        return

    if not address_path.exists():
        print("File {} does not exist.".format(address_path.absolute().as_posix()))
        return

    check_building_have_address(
        buildings_path,
        address_path,
        building_id_field=building_id_field,
        address_building_id_field=address_building_id_field,
    )


if __name__ == "__main__":
    sys.exit(main())
