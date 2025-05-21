#!/usr/bin/python
"""This hook checks Jamf JSON schema custom app manifests for inconsistencies and common issues."""

# References:
# - https://docs.jamf.com/technical-papers/jamf-pro/json-schema/10.19.0/Understanding_the_Structure_of_a_JSON_Schema_Manifest.html
# - https://github.com/Jamf-Custom-Profile-Schemas

import argparse
import json
from datetime import datetime

from pre_commit_hooks.util import PLIST_TYPES, validate_required_keys

# Types found in the Jamf JSON manifests
MANIFEST_TYPES = {
    "array": list,
    "boolean": bool,
    "data": str,
    "date": datetime,
    "float": float,
    "integer": int,
    "number": int,
    "object": dict,
    "real": float,
    "string": str
}

# List keys and their expected item types
MANIFEST_LIST_TYPES = {
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


def validate_key_types(name, manifest, filename):
    """Validation of manifest key types."""

    # Manifest keys and their known types. Omitted keys are left unvalidated.
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
    for manifest_key, expected_type in key_types.items():
        if manifest_key in manifest:
            if not isinstance(manifest[manifest_key], expected_type):
                print(
                    f"{filename}: {name} key {manifest_key} should be type "
                    f"{expected_type}, not type {type(manifest[manifest_key])}"
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

    if type_found not in MANIFEST_TYPES:
        print(f'{filename}: Unexpected "{name}" type "{type_found}"')
        passed = False

    return passed, type_found


def validate_list_item_types(name, manifest, filename):
    """Validation of list member items."""

    passed = True
    for name in MANIFEST_LIST_TYPES:
        if name in manifest:
            try:
                actual_type = type(manifest[name][0])
            except IndexError:
                # Probably an empty array; no way to validate items
                continue
            if isinstance(MANIFEST_LIST_TYPES[name], tuple):
                desired_types = MANIFEST_LIST_TYPES[name]
            else:
                desired_types = [MANIFEST_LIST_TYPES[name]]
            if actual_type not in desired_types:
                print(
                    f'{filename}: "{name}" items should be {MANIFEST_LIST_TYPES[name]}, not {actual_type}'
                )
                passed = False

    return passed


def validate_default(name, prop, type_found, filename):
    """Ensure that default values have the expected type."""
    passed = True

    for test_key in ("default",):
        if test_key in prop:
            if isinstance(prop[test_key], datetime):
                actual_type = str
            else:
                actual_type = type(prop[test_key])
            if actual_type != MANIFEST_TYPES.get(type_found):
                print(
                    f"{filename}: {test_key} value for {name} should be {MANIFEST_TYPES.get(type_found)}, not {type(prop[test_key])}"
                )
                passed = False

    return passed


def validate_urls(name, prop, filename):
    """Ensure that URL values are actual URLs."""
    passed = True

    url_keys = ("pfm_app_url", "pfm_documentation_url")
    for url_key in url_keys:
        if url_key in prop:
            if not prop[url_key].startswith("http"):
                print(
                    f"{filename}: {name} {url_key} value doesn't look like a URL: {prop[url_key]}"
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
        # https://github.com/ProfileCreator/ProfileManifests/wiki/Manifest-Format#example-conditions--exclusions

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
                manifest = json.load(openfile)
        except json.decoder.JSONDecodeError as err:
            print(f"{filename}: json parsing error: {err}")
            retval = 1
            break  # No need to continue checking this file

        # Check for presence of required keys.
        required_keys = ("title", "properties", "description")
        if not validate_required_keys(manifest, filename, required_keys):
            retval = 1
            break  # No need to continue checking this file

        # Ensure top level keys and their list items have expected types.
        if not validate_key_types("<root>", manifest, filename):
            retval = 1
        if not validate_list_item_types("<root>", manifest, filename):
            retval = 1

        # Run checks recursively for all properties
        if "properties" in manifest:
            if not validate_properties(manifest["properties"], filename):
                retval = 1

    return retval


if __name__ == "__main__":
    exit(main())
