#!/usr/bin/python
"""Check Jamf scripts for common issues."""

import argparse

from util import validate_shebangs


def build_argument_parser():
    """Build and return the argument parser."""

    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument("filenames", nargs="*", help="Filenames to check.")
    parser.add_argument(
        "--valid-shebangs",
        nargs="+",
        default=[],
        help="Add other valid shebangs for your environment",
    )
    return parser


def main(argv=None):
    """Main process."""

    # Parse command line arguments.
    argparser = build_argument_parser()
    args = argparser.parse_args(argv)

    retval = 0
    for filename in args.filenames:
        with open(filename, "r", encoding="utf-8") as openfile:
            script_content = openfile.read()

        # Ensure script starts with a shebang of some sort.
        if not script_content.startswith("#!/"):
            print(f"{filename}: missing shebang")
            retval = 1

        # Ensure we're not using env for root-context scripts.
        if script_content.startswith("#!/usr/bin/env"):
            print(f"{filename}: using env for root-context scripts is not recommended")
            retval = 1

        # Ensure all pkginfo scripts have a proper shebang.
        if not validate_shebangs(script_content, filename, args.valid_shebangs):
            print(f"{filename}: does not start with a valid shebang")
            retval = 1

    return retval


if __name__ == "__main__":
    exit(main())
