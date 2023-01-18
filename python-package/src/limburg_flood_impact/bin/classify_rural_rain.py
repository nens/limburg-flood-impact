import argparse
from pathlib import Path
import sys

from .._functions import common_arguments_parser, print_percent
from ..classify_rural_rain import classify_rural_rain


def main():

    parser = argparse.ArgumentParser(prog='ClassifyRuralRain',
                                     description='Classify rural rain.',
                                     epilog='',
                                     parents=[common_arguments_parser()])

    args = parser.parse_args()

    buildings_path: Path = args.buildings
    t10_path: Path = args.t10
    t25_path: Path = args.t25
    t100_path: Path = args.t100

    if not buildings_path.exists():
        raise ValueError("File {} does not exist.".format(buildings_path.absolute().as_posix()))

    if not t10_path.exists():
        raise ValueError("File {} does not exist.".format(t10_path.absolute().as_posix()))

    if not t25_path.exists():
        raise ValueError("File {} does not exist.".format(t25_path.absolute().as_posix()))

    if not t100_path.exists():
        raise ValueError("File {} does not exist.".format(t100_path.absolute().as_posix()))

    classify_rural_rain(buildings_path, t10_path, t25_path, t100_path, print_percent)


if __name__ == "__main__":

    sys.exit(main())
