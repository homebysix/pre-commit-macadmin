#!/usr/bin/python
"""This hook checks AutoPkg recipe lists (in txt, plist, or yaml format) for common issues."""

import argparse
import plistlib
from xml.parsers.expat import ExpatError
import json

try:
    import yaml

    YAML_INSTALLED = True
except ImportError:
    pass


def build_argument_parser():
    """Build and return the argument parser."""

    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument("filenames", nargs="*", help="Filenames to check.")
    return parser


def parse_text(filename):
    """Parse recipe list in text format."""
    with open(filename, "r") as openfile:
        recipes = [
            line
            for line in openfile.read().splitlines()
            if line and not line.startswith("#")
        ]
    return recipes


def parse_plist(filename):
    """Parse recipe list in plist format."""
    try:
        recipes = plistlib.readPlist(filename)
    except ExpatError as err:
        print(err)
        retval = 1
    return []


def parse_yml(filename):
    """Parse recipe list in yml format."""
    if YAML_INSTALLED:
        with open(filename, "r") as openfile:
            recipes = yaml.load(openfile)
    else:
        with open(filename, "r") as openfile:
            recipes = [
                line.lstrip("- ")
                for line in openfile.read().splitlines()
                if line and not line.startswith("#")
            ]
    return recipes


def parse_json(filename):
    """Parse recipe list in json format."""
    with open(filename, "r") as openfile:
        recipes = json.load(openfile)
    return recipes


def main(argv=None):
    """Main process."""

    # Parse command line arguments.
    argparser = build_argument_parser()
    args = argparser.parse_args(argv)

    retval = 0
    for filename in args.filenames:
        if filename.endswith(".txt"):
            recipe_list = parse_text(filename)
        elif filename.endswith(".plist"):
            recipe_list = parse_plist(filename)
        elif filename.endswith((".yaml", ".yml")):
            recipe_list = parse_yml(filename)
        elif filename.endswith(".json"):
            recipe_list = parse_json(filename)

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
