#!/usr/bin/python
# -*- coding: utf-8 -*-

import json
import plistlib
import sys
from datetime import datetime

from ruamel import yaml

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


def load_autopkg_recipe(path):
    """Loads an AutoPkg recipe in plist, yaml, or json format."""
    recipe = None

    if path.endswith(".yaml"):
        try:
            # try to read it as yaml
            with open(path, "rb") as f:
                recipe = yaml.safe_load(f)
        except Exception as err:
            print("{}: yaml parsing error: {}".format(path, err))
    elif path.endswith(".json"):
        try:
            # try to read it as json
            with open(path, "rb") as f:
                recipe = json.load(f)
        except Exception as err:
            print("{}: json parsing error: {}".format(path, err))
    else:
        try:
            # try to read it as a plist
            with open(path, "rb") as f:
                recipe = plistlib.load(f)
        except Exception as err:
            print("{}: plist parsing error: {}".format(path, err))

    return recipe


def validate_required_keys(input_dict, filename, required_keys):
    """Verifies that required_keys are present in dictionary."""
    passed = True
    for req_key in required_keys:
        if not input_dict.get(req_key):
            print("{}: missing required key {}".format(filename, req_key))
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
                "{}: RestartAction key set to unexpected value: {}".format(
                    filename, pkginfo["RestartAction"]
                )
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
                    "{}: pkginfo key {} should be type {}, not type {}".format(
                        filename, pkginfo_key, expected_type, type(pkginfo[pkginfo_key])
                    )
                )
                passed = False

    return passed
