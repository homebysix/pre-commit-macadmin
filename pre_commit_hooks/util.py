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

    # Remap basestring in Python 3
    # Credit: https://github.com/munki/munki/blob/Munki3dev/code/client/munkilib/wrappers.py#L121-L129
    try:
        _ = basestring
    except NameError:
        basestring = str  # pylint: disable=W0622

    # Pkginfo keys and their known types. Omitted keys are left unvalidated.
    # Source: https://github.com/munki/munki/wiki/Supported-Pkginfo-Keys
    # Last updated 2019-03-13.
    pkginfo_types = {
        "additional_startosinstall_options": list,
        "apple_item": bool,
        "autoremove": bool,
        "blocking_applications": list,
        "catalogs": list,
        "category": basestring,
        "copy_local": bool,
        "description": basestring,
        "developer": basestring,
        "display_name": basestring,
        "force_install_after_date": datetime,
        "forced_install": bool,
        "forced_uninstall": bool,
        "icon_name": basestring,
        "installable_condition": basestring,
        "installed_size": int,
        "installer_item_hash": basestring,
        "installer_item_location": basestring,
        "installer_item_size": int,
        "installer_type": basestring,
        "installs": list,
        "items_to_copy": list,
        "installer_choices_xml": list,
        "installer_environment": dict,
        "localized_basestrings": dict,
        "minimum_munki_version": basestring,
        "minimum_os_version": basestring,
        "maximum_os_version": basestring,
        "name": basestring,
        "notes": basestring,
        "PackageCompleteURL": basestring,
        "PackageURL": basestring,
        "package_path": basestring,
        "installcheck_script": basestring,
        "uninstallcheck_script": basestring,
        "OnDemand": bool,
        "postinstall_script": basestring,
        "postuninstall_script": basestring,
        "precache": bool,
        "preinstall_alert": dict,
        "preuninstall_alert": dict,
        "preupgrade_alert": dict,
        "preinstall_script": basestring,
        "preuninstall_script": basestring,
        "receipts": list,
        "requires": list,
        "RestartAction": basestring,
        "supported_architectures": list,
        "suppress_bundle_relocation": bool,
        "unattended_install": bool,
        "unattended_uninstall": bool,
        "uninstall_method": basestring,
        "uninstall_script": basestring,
        "uninstaller_item_location": basestring,
        "uninstallable": bool,
        "update_for": list,
        "version": basestring,
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
