#!/usr/bin/python

import json
import plistlib
import sys
from datetime import datetime

import ruamel.yaml

yaml = ruamel.yaml.YAML(typ="safe")

# Plist data types and their Python equivalents
PLIST_TYPES = {
    "string": str,
    "boolean": bool,
    "dict": dict,
    "dictionary": dict,
    "integer": int,
    "array": list,
    "data": None,  # TODO: How to represent this?
    "float": float,
    "real": float,
    "date": datetime,
}

# List of common shebangs used by Mac admin scripts
# (Can be augmented with --valid-shebangs parameter)
BUILTIN_SHEBANGS = [
    "#!/bin/bash",
    "#!/bin/sh",
    "#!/bin/zsh",
    "#!/usr/bin/osascript",
    "#!/usr/bin/perl",
    "#!/usr/bin/python3",
    "#!/usr/bin/python",  # removed since macOS 12.3
    "#!/usr/bin/ruby",
    "#!/usr/local/munki/munki-python",
    "#!/usr/local/munki/Python.framework/Versions/Current/bin/python3",
]


def load_autopkg_recipe(path):
    """Loads an AutoPkg recipe in plist, yaml, or json format."""
    recipe = None

    if path.endswith(".yaml"):
        try:
            # try to read it as yaml
            with open(path, "rb") as f:
                recipe = yaml.load(f)
        except Exception as err:
            print(f"{path}: yaml parsing error: {err}")
    elif path.endswith(".json"):
        try:
            # try to read it as json
            with open(path, "rb") as f:
                recipe = json.load(f)
        except Exception as err:
            print(f"{path}: json parsing error: {err}")
    else:
        try:
            # try to read it as a plist
            with open(path, "rb") as f:
                recipe = plistlib.load(f)
        except Exception as err:
            print(f"{path}: plist parsing error: {err}")

    return recipe


def validate_required_keys(input_dict, filename, required_keys):
    """Verifies that required_keys are present in dictionary."""
    passed = True
    for req_key in required_keys:
        if not input_dict.get(req_key):
            print(f"{filename}: missing required key {req_key}")
            passed = False
    return passed


def validate_restart_action_key(pkginfo, filename):
    """Verifies that required_keys are present in pkginfo dictionary."""
    passed = True
    allowed_values = (
        "RequireShutdown",
        "RequireRestart",
        "RecommendRestart",
        "RequireLogout",
        "None",
    )
    if "RestartAction" in pkginfo:
        if pkginfo["RestartAction"] not in allowed_values:
            print(
                f"{filename}: RestartAction key set to unexpected value: {pkginfo['RestartAction']}"
            )
            passed = False
    return passed


def validate_pkginfo_key_types(pkginfo, filename):
    """Validation of pkginfo key types.

    Used for AutoPkg- and Munki-related hooks.
    """

    # Remap string type to support unicode in both Python 2 and 3
    string = basestring if sys.version_info.major == 2 else str

    # Pkginfo keys and their known types. Omitted keys are left unvalidated.
    # Source: https://github.com/munki/munki/wiki/Supported-Pkginfo-Keys
    # Last updated 2019-03-13.
    pkginfo_types = {
        "additional_startosinstall_options": list,
        "apple_item": bool,
        "autoremove": bool,
        "blocking_applications": list,
        "catalogs": list,
        "category": string,
        "copy_local": bool,
        "description": string,
        "developer": string,
        "display_name": string,
        "force_install_after_date": datetime,
        "forced_install": bool,
        "forced_uninstall": bool,
        "icon_name": string,
        "installable_condition": string,
        "installed_size": int,
        "installer_item_hash": string,
        "installer_item_location": string,
        "installer_item_size": int,
        "installer_type": string,
        "installs": list,
        "items_to_copy": list,
        "installer_choices_xml": list,
        "installer_environment": dict,
        "localized_strings": dict,
        "minimum_munki_version": string,
        "minimum_os_version": string,
        "maximum_os_version": string,
        "name": string,
        "notes": string,
        "PackageCompleteURL": string,
        "PackageURL": string,
        "package_path": string,
        "installcheck_script": string,
        "uninstallcheck_script": string,
        "OnDemand": bool,
        "postinstall_script": string,
        "postuninstall_script": string,
        "precache": bool,
        "preinstall_alert": dict,
        "preuninstall_alert": dict,
        "preupgrade_alert": dict,
        "preinstall_script": string,
        "preuninstall_script": string,
        "receipts": list,
        "requires": list,
        "RestartAction": string,
        "supported_architectures": list,
        "suppress_bundle_relocation": bool,
        "unattended_install": bool,
        "unattended_uninstall": bool,
        "uninstall_method": string,
        "uninstall_script": string,
        "uninstaller_item_location": string,
        "uninstallable": bool,
        "update_for": list,
        "version": string,
    }

    passed = True
    for pkginfo_key, expected_type in pkginfo_types.items():
        if pkginfo_key in pkginfo:
            if not isinstance(pkginfo[pkginfo_key], expected_type):
                print(
                    f"{filename}: pkginfo key {pkginfo_key} should be type "
                    f"{expected_type}, not type {type(pkginfo[pkginfo_key])}"
                )
                passed = False

    return passed


def validate_shebangs(script_content, filename, addl_shebangs=[]):
    """Verifies that scripts begin with a valid shebang."""
    passed = True
    shebangs = BUILTIN_SHEBANGS + addl_shebangs
    if not any(script_content.startswith(x + "\n") for x in shebangs):
        print(f"{filename}: does not start with a valid shebang")
        passed = False
    return passed
