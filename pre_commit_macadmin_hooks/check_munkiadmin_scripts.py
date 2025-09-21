#!/usr/bin/python
"""This hook ensures MunkiAdmin scripts are executable."""

import argparse
import os
from typing import List, Optional

from pre_commit_macadmin_hooks.util import validate_shebangs


def build_argument_parser() -> argparse.ArgumentParser:
    """Build and return the argument parser."""

    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument("filenames", nargs="*", help="Filenames to check.")
    return parser


def main(argv: Optional[List[str]] = None) -> int:
    """Main process."""

    # Parse command line arguments.
    argparser = build_argument_parser()
    args = argparser.parse_args(argv)

    retval = 0
    for filename in args.filenames:

        # Ensure scripts are named properly.
        # https://github.com/hjuutilainen/munkiadmin/blob/4f4e96da1f1c7a4dfe7da59d88f1ef68ee02b8f2/MunkiAdmin/Singletons/MAMunkiRepositoryManager.m#L23
        prefixes = ["manifest", "pkginfo", "repository"]
        actions = ["custom", "postopen", "postsave", "presave"]
        ma_script_prefixes = [f"{p}-{a}" for p in prefixes for a in actions]
        if not any(
            os.path.basename(filename).startswith(prefix)
            for prefix in ma_script_prefixes
        ):
            print(f"{filename}: does not start with a valid MunkiAdmin script prefix")
            retval = 1

        # Ensure scripts are executable
        if not os.access(filename, os.X_OK):
            print(f"{filename}: not executable")
            retval = 1

        # Ensure scripts have a proper shebang
        with open(filename, encoding="utf-8") as openfile:
            script_content = openfile.read()
        if not validate_shebangs(script_content, filename):
            print(f"{filename}: does not start with a valid shebang")
            retval = 1

    return retval


if __name__ == "__main__":
    exit(main())
