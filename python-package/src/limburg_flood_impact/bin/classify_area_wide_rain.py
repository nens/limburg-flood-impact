import argparse
from pathlib import Path
import sys

from .._functions import common_arguments_parser, print_percent
from ..classify_area_wide_rain import classify_area_wide_rain


def main():

    parser = argparse.ArgumentParser(prog='ClassifyAreaWideRain',
                                     description='Classify area wide rain.',
                                     epilog='',
                                     parents=[common_arguments_parser()])

    args = parser.parse_args()

    buildings_path: Path = args.buildings
    t10_path: Path = args.t10
    t25_path: Path = args.t25
    t100_path: Path = args.t100

    if not buildings_path.exists():
        print("File {} does not exist.".format(buildings_path.absolute().as_posix()))
        return

    if not t10_path.exists():
        print("File {} does not exist.".format(t10_path.absolute().as_posix()))
        return

    if not t25_path.exists():
        print("File {} does not exist.".format(t25_path.absolute().as_posix()))
        return

    if not t100_path.exists():
        print("File {} does not exist.".format(t100_path.absolute().as_posix()))
        return

    classify_area_wide_rain(buildings_path, t10_path, t25_path, t100_path, print_percent)


if __name__ == "__main__":

    sys.exit(main())
