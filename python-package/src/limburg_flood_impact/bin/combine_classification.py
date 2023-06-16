import argparse
import sys
from pathlib import Path

from .._functions import print_percent
from ..combine_classification import combine_classification


def main():
    parser = argparse.ArgumentParser(
        prog="CombineClassification",
        description="Combine classifications.",
        epilog="",
    )

    parser.add_argument(
        "-b",
        "--buildings",
        type=lambda p: Path(p).absolute(),
        help="Path to the file with buildings.",
        required=True,
    )

    args = parser.parse_args()

    buildings_path: Path = args.buildings

    if not buildings_path.exists():
        print("File {} does not exist.".format(buildings_path.absolute().as_posix()))
        return

    combine_classification(buildings_path, print_percent)


if __name__ == "__main__":
    sys.exit(main())
