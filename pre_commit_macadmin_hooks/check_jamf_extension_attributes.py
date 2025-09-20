#!/usr/bin/python
"""Check Jamf extension attributes for common issues."""

import argparse
import re
from typing import List, Optional

from pre_commit_macadmin_hooks.util import validate_shebangs


def build_argument_parser() -> argparse.ArgumentParser:
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


def main(argv: Optional[List[str]] = None) -> int:
    """Main process."""

    # Parse command line arguments.
    argparser = build_argument_parser()
    args = argparser.parse_args(argv)

    retval = 0
    for filename in args.filenames:
        with open(filename, encoding="utf-8") as openfile:
            ea_content = openfile.read()

        # Ensure script contains both <result> and </result> tags
        if "<result>" not in ea_content or "</result>" not in ea_content:
            print(f"{filename}: missing <result> and/or </result> tags")
            retval = 1

        # Ensure result tags are in proper order (open then close)
        all_results = len(re.findall(r"result.*\/result", ea_content))
        proper_results = len(re.findall(r"<result>.*<\/result>", ea_content))
        if proper_results < all_results:
            print(f"{filename}: has incomplete <result> tags")
            retval = 1

        # Ensure all pkginfo scripts have a proper shebang.
        if not validate_shebangs(ea_content, filename, args.valid_shebangs):
            print(f"{filename}: does not start with a valid shebang")
            retval = 1

    return retval


if __name__ == "__main__":
    exit(main())
