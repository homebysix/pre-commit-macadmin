#!/usr/bin/python

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

    # Pkginfo keys and their known types. Omitted keys are left unvalidated.
    # Source: https://github.com/munki/munki/wiki/Supported-Pkginfo-Keys
    # Last updated 2019-03-13.
    pkginfo_types = {
        "additional_startosinstall_options": list,
        "apple_item": bool,
        "autoremove": bool,
        "blocking_applications": list,
        "catalogs": list,
        "category": str,
        "copy_local": bool,
        "description": str,
        "developer": str,
        "display_name": str,
        "force_install_after_date": datetime,
        "forced_install": bool,
        "forced_uninstall": bool,
        "icon_name": str,
        "installable_condition": str,
        "installed_size": int,
        "installer_item_hash": str,
        "installer_item_location": str,
        "installer_item_size": int,
        "installer_type": str,
        "installs": list,
        "items_to_copy": list,
        "installer_choices_xml": list,
        "installer_environment": dict,
        "localized_strs": dict,
        "minimum_munki_version": str,
        "minimum_os_version": str,
        "maximum_os_version": str,
        "name": str,
        "notes": str,
        "PackageCompleteURL": str,
        "PackageURL": str,
        "package_path": str,
        "installcheck_script": str,
        "uninstallcheck_script": str,
        "OnDemand": bool,
        "postinstall_script": str,
        "postuninstall_script": str,
        "precache": bool,
        "preinstall_alert": dict,
        "preuninstall_alert": dict,
        "preupgrade_alert": dict,
        "preinstall_script": str,
        "preuninstall_script": str,
        "receipts": list,
        "requires": list,
        "RestartAction": str,
        "supported_architectures": list,
        "suppress_bundle_relocation": bool,
        "unattended_install": bool,
        "unattended_uninstall": bool,
        "uninstall_method": str,
        "uninstall_script": str,
        "uninstaller_item_location": str,
        "uninstallable": bool,
        "update_for": list,
        "version": str,
    }

    retbool = True
    for pkginfo_key, expected_type in pkginfo_types.items():
        if pkginfo_key in pkginfo:
            if not isinstance(pkginfo[pkginfo_key], expected_type):
                print(
                    "{}: pkginfo key {} should be type {}, not type {}".format(
                        filename, pkginfo_key, expected_type, type(pkginfo[pkginfo_key])
                    )
                )
                retbool = False

    return retbool
