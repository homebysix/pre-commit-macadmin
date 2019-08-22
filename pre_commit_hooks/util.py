#!/usr/bin/python

import sys
from datetime import datetime


def validate_required_keys(plist, filename, required_keys):
    """Verifies that required_keys are present in dictionary plist."""
    passed = True
    for req_key in required_keys:
        if not plist.get(req_key):
            print("{}: missing required key {}".format(filename, req_key))
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
