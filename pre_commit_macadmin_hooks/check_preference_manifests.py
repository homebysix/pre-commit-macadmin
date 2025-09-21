#!/usr/bin/python
"""This hook checks Apple preference manifest plists for inconsistencies and common issues."""

# References:
# - https://developer.apple.com/library/archive/documentation/MacOSXServer/Conceptual/Preference_Manifest_Files/Preface/Preface.html
# - https://github.com/ProfileCreator/ProfileManifests/wiki/Manifest-Format
# - https://mosen.github.io/profiledocs/manifest.html

import argparse
import plistlib
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple
from xml.parsers.expat import ExpatError

from pre_commit_macadmin_hooks.util import PLIST_TYPES

# List keys and their expected item types
PFM_LIST_TYPES = {
    "pfm_allowed_file_types": str,
    "pfm_conditionals": dict,
    "pfm_exclude": dict,
    "pfm_subkeys": dict,
    "pfm_target_conditions": str,
    "pfm_targets": str,
    "pfm_upk_input_keys": str,
    "pfm_n_platforms": str,
    "pfm_platforms": str,
    "pfm_range_list_titles": str,
}


def build_argument_parser() -> argparse.ArgumentParser:
    """Build and return the argument parser."""

    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument("filenames", nargs="*", help="Filenames to check.")
    return parser


def validate_required_keys(
    input_dict: Dict[str, Any],
    required_keys: Tuple[str, ...],
    dict_name: str,
    filename: str,
) -> bool:
    """Verifies that required_keys are present in dictionary."""
    passed = True
    for req_key in required_keys:
        if input_dict.get(req_key, "") == "":
            print(f"{filename}: {dict_name} missing required key {req_key}")
            passed = False
    return passed


def validate_manifest_key_types(manifest: Dict[str, Any], filename: str) -> bool:
    """Validation of manifest key types."""

    # manifest keys and their known types. Omitted keys are left un-validated.
    # Last updated 2021-12-03.
    key_types = {
        "pfm_conditionals": list,
        "pfm_description": str,
        "pfm_domain": str,
        "pfm_exclude": list,
        "pfm_format_version": (int, float),
        "pfm_format": str,
        "pfm_name": str,
        "pfm_range_list": list,
        "pfm_range_max": (int, float),
        "pfm_range_min": (int, float),
        "pfm_repetition_max": int,
        "pfm_repetition_min": int,
        "pfm_require": str,
        "pfm_required": bool,
        "pfm_subkeys": list,
        "pfm_targets": list,
        "pfm_title": str,
        "pfm_type": str,
        "pfm_version": (int, float),
        # Extended manifest format keys:
        "pfm_allowed_file_types": list,
        "pfm_app_deprecated": str,
        "pfm_app_max": str,
        "pfm_app_min": str,
        "pfm_app_url": str,
        "pfm_default_copy": str,
        "pfm_date_allow_past": bool,
        "pfm_date_style": str,
        "pfm_description_extended": str,
        "pfm_description_reference": str,
        "pfm_documentation_url": str,
        "pfm_enabled": bool,
        "pfm_excluded": bool,
        "pfm_hidden": str,
        # "pfm_icon": data,
        "pfm_interaction": str,
        "pfm_ios_deprecated": str,
        "pfm_ios_max": str,
        "pfm_ios_min": str,
        "pfm_last_modified": datetime,
        "pfm_macos_deprecated": str,
        "pfm_macos_max": str,
        "pfm_macos_min": str,
        "pfm_note": str,
        "pfm_n_platforms": list,
        "pfm_platforms": list,
        "pfm_range_list_allow_custom_value": bool,
        "pfm_range_list_titles": list,
        "pfm_segments": dict,
        "pfm_sensitive": bool,
        "pfm_subdomain": str,
        "pfm_substitution_variables": dict,
        "pfm_supervised": bool,
        "pfm_type_input": str,
        "pfm_tvos_deprecated": str,
        "pfm_tvos_max": str,
        "pfm_tvos_min": str,
        "pfm_unique": bool,
        "pfm_user_approved": bool,
        "pfm_value_copy": str,
        "pfm_value_decimal_places": int,
        "pfm_value_inverted": bool,
        "pfm_value_import_processor": str,
        "pfm_value_info_processor": str,
        "pfm_value_processor": str,
        "pfm_value_unique": bool,
        "pfm_value_unit": str,
        "pfm_view": str,
    }

    passed = True
    for manifest_key, expected_type in key_types.items():
        if manifest_key in manifest:
            if not isinstance(manifest[manifest_key], expected_type):  # type: ignore[arg-type]
                print(
                    f"{filename}: manifest key {manifest_key} should be type "
                    f"{expected_type}, not type {type(manifest[manifest_key])}"
                )
                passed = False

    return passed


def validate_list_item_types(manifest, filename):
    """Validation of list member items."""

    passed = True
    for name in PFM_LIST_TYPES:
        if name in manifest:
            try:
                actual_type = type(manifest[name][0])
            except IndexError:
                # Probably an empty array; no way to validate items
                continue
            if actual_type is not PFM_LIST_TYPES[name]:
                print(
                    f'{filename}: "{name}" items should be type '
                    f"{PFM_LIST_TYPES[name]}, not type {actual_type}"
                )
                passed = False

    return passed


def validate_required_subkeys(subkey, req_keys, filename):
    """Ensure specific keys are defined in subkeys."""
    passed = True

    for subsubkey in subkey.get("pfm_subkeys", []):
        if subsubkey.get("pfm_name"):
            display_name = subsubkey["pfm_name"]
        elif subkey.get("pfm_name"):
            display_name = subkey["pfm_name"] + " subkey"
        else:
            display_name = "<unnamed key> subkey"
        if not validate_required_keys(subsubkey, req_keys, display_name, filename):
            passed = False

    return passed


def validate_pfm_type_strings(subkey, filename):
    """Ensure subkey pfm_type strings are as expected."""
    passed = True

    pfm_depr_types = ("union policy", "url")
    if subkey["pfm_type"] in pfm_depr_types:
        print(f'{filename}: WARNING: Subkey type "{subkey["pfm_type"]}" is deprecated')
        # passed = False
    elif subkey["pfm_type"] not in PLIST_TYPES:
        print(
            f'{filename}: Unexpected subkey type {subkey["pfm_type"]} for {subkey.get("pfm_name")}'
        )
        passed = False

    return passed


def validate_subkey_known_types(subkey, filename):
    """Ensure specific subkey names have expected type."""
    passed = True

    pfm_name_types = {
        "PayloadCertificateAnchorUUID": "array",
        "PayloadCertificateFileName": "string",
        "PayloadCertificateUUID": "string",
        "PayloadContent": ("data", "string", "dictionary", "dict"),
        "PayloadDescription": "string",
        "PayloadDisplayName": "string",
        "PayloadExpirationDate": "date",
        "PayloadIdentification": ("dictionary", "dict"),
        "PayloadIdentifier": "string",
        "PayloadOrganization": "string",
        "PayloadRemovalDisallowed": "boolean",
        "PayloadType": "string",
        "PayloadUUID": "string",
        "PayloadVersion": ("integer", "float"),
    }
    if subkey.get("pfm_name", "") in pfm_name_types:
        if isinstance(pfm_name_types[subkey["pfm_name"]], tuple):
            name_types = pfm_name_types[subkey["pfm_name"]]
        else:
            name_types = [pfm_name_types[subkey["pfm_name"]]]
        if subkey["pfm_type"] not in name_types:
            print(
                f'{filename}: Subkey name "{subkey["pfm_name"]}" should be '
                f'type "string", not type "{subkey["pfm_type"]}"'
            )
            passed = False

    return passed


def validate_pfm_required(subkey, filename):
    """Ensure pfm_require and pfm_required keys have expected values."""
    passed = True

    # Source: https://github.com/ProfileCreator/ProfileManifests/wiki/Manifest-Format
    require_options = ("always", "always-nested", "push")
    if "pfm_require" in subkey:
        if subkey["pfm_require"] not in require_options:
            print(
                f'{filename}: "pfm_require" value "{subkey["pfm_require"]}" '
                f"should be one of: {require_options}"
            )
            passed = False
    if "pfm_required" in subkey:
        if subkey["pfm_required"] is not True:
            print(
                f'{filename}: "pfm_required" value "{subkey["pfm_required"]}" should be True, if used at all'
            )
            passed = False
    if "pfm_required" in subkey and "pfm_require" in subkey:
        print(f'{filename}: No need to specify both "pfm_required" and "pfm_require"')

    return passed


def validate_pfm_targets(subkey, filename):
    """Ensure pfm_targets key has expected values."""
    passed = True

    target_options = ("user", "user-managed", "system", "system-managed")
    if "pfm_targets" in subkey:
        if any([x not in target_options for x in subkey["pfm_targets"]]):
            print(
                f'{filename}: "pfm_targets" values should be one of: {target_options}'
            )
            passed = False

    return passed


def validate_pfm_default(subkey, filename):
    """Ensure that default values have the expected type."""
    passed = True

    if "pfm_type" in subkey:
        # TODO: Should we validate pfm_value_placeholder here too?
        for test_key in ("pfm_default",):
            if test_key in subkey:
                # TODO: Should the default for list types be the type of the first list item, or <list> itself?
                # if PLIST_TYPES[subkey["pfm_type"]] == list:
                #     try:
                #         desired_type = type(subkey["pfm_subkeys"][0])
                #     except IndexError:
                #         # Unknown desired type
                #         continue
                # else:
                desired_type = PLIST_TYPES[subkey["pfm_type"]]
                if not isinstance(subkey[test_key], desired_type):
                    print(
                        f"{filename}: {test_key} value for {subkey.get('pfm_name')} should be type "
                        f"{PLIST_TYPES[subkey['pfm_type']]}, not type {type(subkey[test_key])}"
                    )
                    passed = False

    return passed


def validate_urls(subkey, filename):
    """Ensure that URL values are actual URLs."""
    passed = True

    url_keys = ("pfm_app_url", "pfm_documentation_url")
    for url_key in url_keys:
        if url_key in subkey:
            if len(subkey[url_key]) == 0:
                print(f"{filename}: {url_key} URL value is empty.")
                passed = False
            elif not subkey[url_key].startswith("http"):
                print(
                    f"{filename}: {url_key} value doesn't look like a URL: {subkey[url_key]}"
                )
                passed = False

    return passed


def validate_platforms(subkey, filename):
    """Ensure that `pfm_platforms` and `pfm_n_platforms` values are valid."""
    passed = True

    valid_platforms = ["macOS", "iOS", "tvOS"]

    platform_keys = ["pfm_platforms", "pfm_n_platforms"]
    for platform_key in platform_keys:
        if platform_key in subkey:
            for platform in subkey[platform_key]:
                if platform not in valid_platforms:
                    print(
                        f"{filename}: {platform_key} value doesn't look like a valid platform string: {platform}"
                    )
                    passed = False

    return passed


def validate_subkeys(subkeys, filename):
    """Given a list of subkeys, run validation on their contents."""
    passed = True
    type_passed = True

    for subkey in subkeys:

        # Check for presence of required subkeys
        # (Not calling validate_required_keys() directly because the output would not be
        # specific enough to indicate *where* in the manifest the problem exists.)
        # Example of validate_required_keys() output:
        #   menu.nomad.NoMADPro.plist: <unnamed key> missing required key pfm_type
        # Example of validate_required_subkeys() output:
        #   menu.nomad.NoMADPro.plist: ChangePasswordItem subkey missing required key pfm_type
        if subkey["pfm_type"] != "array":
            # pfm_name is required only if the pfm_type is not array
            required_keys = ("pfm_type", "pfm_name")
        else:
            required_keys = ("pfm_type",)
        if not validate_required_subkeys(subkey, required_keys, filename):
            passed = False
            break  # No need to continue checking this list of subkeys

        # Check for rogue pfm_type strings and deprecated keys.
        if not validate_pfm_type_strings(subkey, filename):
            passed = False
            type_passed = False

        # TODO: Suggest adding a title if one is missing
        # if "pfm_title" not in subkey:
        #     print(
        #         "WARNING: Recommend adding a pfm_title to %s"
        #         % subkey.get("pfm_name", "<unnamed key>")
        #     )

        # Check that list items are of the expected type
        if not validate_list_item_types(subkey, filename):
            passed = False

        # Check for specific names to have specific types
        if not validate_subkey_known_types(subkey, filename):
            passed = False

        # Check for specific key names to match specific values
        if not validate_pfm_required(subkey, filename):
            passed = False
        if not validate_pfm_targets(subkey, filename):
            passed = False

        # Check default values to ensure consistent type
        if type_passed and not validate_pfm_default(subkey, filename):
            passed = False

        # Validate URLs
        if not validate_urls(subkey, filename):
            passed = False

        # Validate platforms
        if not validate_platforms(subkey, filename):
            passed = False

        # TODO: Validate pfm_conditionals
        # https://github.com/ProfileCreator/ProfileManifests/wiki/Manifest-Format#example-conditions--exclusions

        # Recursively validate sub-sub-keys
        if "pfm_subkeys" in subkey:
            if not validate_subkeys(subkey["pfm_subkeys"], filename):
                passed = False

    return passed


def main(argv: Optional[List[str]] = None) -> int:
    """Main process."""

    # Parse command line arguments.
    argparser = build_argument_parser()
    args = argparser.parse_args(argv)

    retval = 0
    for filename in args.filenames:
        try:
            with open(filename, "rb") as openfile:
                manifest = plistlib.load(openfile)
        except (ExpatError, ValueError) as err:
            print(f"{filename}: plist parsing error: {err}")
            retval = 1
            continue  # No need to continue checking this file

        # Check for presence of required keys.
        required_keys = ("pfm_title", "pfm_domain", "pfm_description")
        if not validate_required_keys(manifest, required_keys, "<root dict>", filename):
            retval = 1
            continue  # No need to continue checking this file

        # Ensure pfm_format_version has expected value
        if manifest.get("pfm_format_version", 1) != 1:
            print(
                f"{filename}: pfm_format_version should be 1, not {manifest.get('pfm_format_version')} "
                "(https://github.com/ProfileCreator/ProfileManifests"
                "/wiki/Manifest-Format-Versions)"
            )
            retval = 1

        # Ensure platform values are valid
        if not validate_platforms(manifest, filename):
            retval = 1

        # Ensure top level keys and their list items have expected types.
        if not validate_manifest_key_types(manifest, filename):
            retval = 1
        if not validate_list_item_types(manifest, filename):
            retval = 1

        # Run checks recursively for all subkeys
        if "pfm_subkeys" in manifest:
            if not validate_subkeys(manifest["pfm_subkeys"], filename):
                retval = 1

    return retval


if __name__ == "__main__":
    exit(main())
