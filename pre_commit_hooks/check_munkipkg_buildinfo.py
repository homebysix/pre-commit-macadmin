#!/usr/bin/python
"""Check MunkiPkg build-info files to ensure they are valid."""

import argparse
import plistlib
from xml.parsers.expat import ExpatError
import json
import ruamel.yaml

yaml = ruamel.yaml.YAML(typ="safe")


def build_argument_parser():
    """Build and return the argument parser."""

    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument("filenames", nargs="*", help="Filenames to check.")
    return parser


def main(argv=None):
    """Main process."""

    # Parse command line arguments.
    argparser = build_argument_parser()
    args = argparser.parse_args(argv)

    retval = 0
    for filename in args.filenames:
        if filename.endswith(".plist"):
            try:
                buildinfo = plistlib.readPlist(filename)
            except (ExpatError, ValueError) as err:
                print("{}: plist parsing error: {}".format(filename, err))
                retval = 1
        elif filename.endswith((".yaml", ".yml")):
            try:
                with open(filename, "r") as openfile:
                    buildinfo = yaml.load(openfile, Loader=yaml.FullLoader)
            except Exception as err:
                print("{}: yaml parsing error: {}".format(filename, err))
                retval = 1
        elif filename.endswith(".json"):
            try:
                with open(filename, "r") as openfile:
                    buildinfo = json.load(openfile)
            except Exception as err:
                print("{}: json parsing error: {}".format(filename, err))
                retval = 1

        if not buildinfo or not isinstance(buildinfo, dict):
            print("{}: invalid build-info file")
            retval = 1

    return retval


if __name__ == "__main__":
    exit(main())
