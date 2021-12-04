#!/usr/bin/python
# -*- coding: utf-8 -*-
"""This hook checks Jamf JSON schemas for inconsistencies and common issues."""

# References:
# - https://developer.apple.com/library/archive/documentation/MacOSXServer/Conceptual/Preference_schema_Files/Preface/Preface.html
# - https://github.com/ProfileCreator/Profileschemas/wiki/schema-Format
# - https://mosen.github.io/profiledocs/schema.html

import argparse
import json
from datetime import datetime

from pre_commit_hooks.util import PLIST_TYPES, validate_required_keys

# Types found in the Jamf JSON schemas
SCHEMA_TYPES = (
    "string",
    "boolean",
    "object",
    "integer",
    "array",
    "data",
    "float",
    "real",
    "date",
)

# List keys and their expected item types
SCHEMA_LIST_TYPES = {
    "enum_titles": str,
    "enum": (str, int, float, bool),
    "links": dict,
    "anyOf": dict,
}


def build_argument_parser():
    """Build and return the argument parser."""

    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument("filenames", nargs="*", help="Filenames to check.")
    return parser


def validate_schema_key_types(name, schema, filename):
    """Validation of schema key types."""

    # Schema keys and their known types. Omitted keys are left unvalidated.
    key_types = {
        "description": str,
        "enum_titles": list,
        "enum": list,
        "href": str,
        "items": dict,
        "links": list,
        "options": dict,
        "pattern": str,
        "properties": dict,
        "property_order": int,
        "rel": str,
        "title": str,
        "type": str,
        "anyOf": list,
    }

    passed = True
    for schema_key, expected_type in key_types.items():
        if schema_key in schema:
            if not isinstance(schema[schema_key], expected_type):
                print(
                    "{}: {} key {} should be type {}, not type {}".format(
                        filename,
                        name,
                        schema_key,
                        expected_type,
                        type(schema[schema_key]),
                    )
                )
                passed = False

    return passed


def validate_type(name, property, filename):
    """Ensure property type keu is present and among expected values."""
    passed = True
    type_found = None

    if "type" in property:
        type_found = property.get("type")
    elif "anyOf" in property:
        for t in [x.get("type") for x in property["anyOf"]]:
            if t != "null":
                type_found = t
                break

    if type_found not in SCHEMA_TYPES:
        print('{}: Unexpected "{}" type "{}"'.format(filename, name, type_found))
        passed = False

    return passed, type_found


def validate_list_item_types(name, schema, filename):
    """Validation of list member items."""

    passed = True
    for name in SCHEMA_LIST_TYPES:
        if name in schema:
            try:
                actual_type = type(schema[name][0])
            except IndexError:
                # Probably an empty array; no way to validate items
                continue
            if isinstance(SCHEMA_LIST_TYPES[name], tuple):
                desired_types = SCHEMA_LIST_TYPES[name]
            else:
                desired_types = [SCHEMA_LIST_TYPES[name]]
            if actual_type not in desired_types:
                print(
                    '{}: "{}" items should be {}, not {}'.format(
                        filename, name, SCHEMA_LIST_TYPES[name], actual_type
                    )
                )
                passed = False

    return passed


def validate_default(name, property, type_found, filename):
    """Ensure that default values have the expected type."""
    passed = True

    for test_key in ("default",):
        if test_key in property:
            if type(property[test_key]) == datetime:
                actual_type = str
            else:
                actual_type = type(property[test_key])
            if actual_type != PLIST_TYPES[type_found]:
                print(
                    "{}: {} value for {} should be {}, not {}".format(
                        filename,
                        test_key,
                        name,
                        PLIST_TYPES[type_found],
                        type(property[test_key]),
                    )
                )
                passed = False

    return passed


def validate_urls(name, property, filename):
    """Ensure that URL values are actual URLs."""
    passed = True

    url_keys = ("pfm_app_url", "pfm_documentation_url")
    for url_key in url_keys:
        if url_key in property:
            if not property[url_key].startswith("http"):
                print(
                    "{}: {} {} value doesn't look like a URL: {}".format(
                        filename,
                        name,
                        url_key,
                        property[url_key],
                    )
                )
                passed = False

    return passed


def validate_properties(properties, filename):
    """Given a list of properties, run validation on their contents."""
    passed = True

    for name, prop in properties.items():
        if name.strip() == "":
            name = "<unnamed property>"

        # Validate URLs
        if not validate_urls(name, prop, filename):
            passed = False

        # Check for presence of "type" key.
        type_ok, type_found = validate_type(name, prop, filename)
        if not type_ok:
            passed = False
            break  # No need to continue checking this property

        # Check that list items are of the expected type
        if not validate_list_item_types(name, prop, filename):
            passed = False

        # Check default values to ensure consistent type
        if not validate_default(name, prop, type_found, filename):
            passed = False

        # TODO: Validate pfm_conditionals
        # https://github.com/ProfileCreator/Profileschemas/wiki/schema-Format#example-conditions--exclusions

        # TODO: Process $ref references

        # Recursively validate sub-sub-properties
        if "properties" in prop:
            if not validate_properties(prop["properties"], filename):
                passed = False

    return passed


def main(argv=None):
    """Main process."""

    # Parse command line arguments.
    argparser = build_argument_parser()
    args = argparser.parse_args(argv)

    retval = 0
    for filename in args.filenames:
        try:
            with open(filename, "rb") as openfile:
                schema = json.load(openfile)
        except json.decoder.JSONDecodeError as err:
            print("{}: json parsing error: {}".format(filename, err))
            retval = 1
            break  # No need to continue checking this file

        # Check for presence of required keys.
        required_keys = ("title", "properties", "description")
        if not validate_required_keys(schema, filename, required_keys):
            retval = 1
            break  # No need to continue checking this file

        # Ensure top level keys and their list items have expected types.
        if not validate_schema_key_types("<root>", schema, filename):
            retval = 1
        if not validate_list_item_types("<root>", schema, filename):
            retval = 1

        # Run checks recursively for all properties
        if "properties" in schema:
            if not validate_properties(schema["properties"], filename):
                retval = 1

    return retval


if __name__ == "__main__":
    exit(main())
