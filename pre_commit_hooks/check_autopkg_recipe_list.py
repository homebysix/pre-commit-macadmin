#!/usr/bin/python
"""This hook checks AutoPkg recipe lists (in txt, plist, yaml, or json format) for common issues."""

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
        if filename.endswith(".txt"):
            with open(filename, "r") as openfile:
                recipe_list = [
                    line
                    for line in openfile.read().splitlines()
                    if line and not line.startswith("#")
                ]
        elif filename.endswith(".plist"):
            try:
                recipe_list = plistlib.readPlist(filename)
            except (ExpatError, ValueError) as err:
                print("{}: plist parsing error: {}".format(filename, err))
                retval = 1
        elif filename.endswith((".yaml", ".yml")):
            try:
                with open(filename, "r") as openfile:
                    recipe_list = yaml.load(openfile, Loader=yaml.FullLoader)
            except Exception as err:
                print("{}: yaml parsing error: {}".format(filename, err))
                retval = 1
        elif filename.endswith(".json"):
            try:
                with open(filename, "r") as openfile:
                    recipe_list = json.load(openfile)
            except Exception as err:
                print("{}: json parsing error: {}".format(filename, err))
                retval = 1

        if not recipe_list or not isinstance(recipe_list, list):
            print("{}: invalid recipe list")
            retval = 1
        else:
            if any((".munki" in recipe for recipe in recipe_list)):
                if "MakeCatalogs" not in recipe_list[-1]:
                    print("{}: MakeCatalogs should be the last item in the list")
                    retval = 1

    return retval


if __name__ == "__main__":
    exit(main())
