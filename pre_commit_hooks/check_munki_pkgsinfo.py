#!/usr/bin/python
# -*- coding: utf-8 -*-
"""This hook checks Munki pkginfo files to ensure they are valid."""

import argparse
import os
import plistlib
from xml.parsers.expat import ExpatError

from pre_commit_hooks.util import (
    validate_pkginfo_key_types,
    validate_required_keys,
    validate_restart_action_key,
)


def build_argument_parser():
    """Build and return the argument parser."""

    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument("--categories", nargs="+", help="List of approved categories.")
    parser.add_argument("--catalogs", nargs="+", help="List of approved catalogs.")
    parser.add_argument(
        "--required-keys",
        nargs="+",
        default=["description", "name"],
        help="List of required top-level keys.",
    )
    parser.add_argument(
        "--require-pkg-blocking-apps",
        action="store_true",
        help="Require a blocking_applications array for pkg installers.",
    )
    parser.add_argument("filenames", nargs="*", help="Filenames to check.")
    return parser


def main(argv=None):
    """Main process."""

    # Typical extensions for installer packages.
    pkg_exts = ("pkg", "dmg")
    dupe_suffixes = ["__{}.{}".format(i, ext) for ext in pkg_exts for i in range(1, 9)]

    # RestartAction values that obviate the need to check blocking applications.
    blocking_actions = ("RequireRestart", "RequireShutdown", "RequireLogout")

    # Parse command line arguments.
    argparser = build_argument_parser()
    args = argparser.parse_args(argv)

    retval = 0
    for filename in args.filenames:
        try:
            with open(filename, "rb") as openfile:
                pkginfo = plistlib.load(openfile)
        except (ExpatError, ValueError) as err:
            print("{}: plist parsing error: {}".format(filename, err))
            retval = 1

        # Check for presence of required pkginfo keys.
        if args.required_keys:
            if not validate_required_keys(pkginfo, filename, args.required_keys):
                retval = 1
                break  # No need to continue checking this file

        # Ensure pkginfo keys have expected types.
        if not validate_pkginfo_key_types(pkginfo, filename):
            retval = 1

        # Validate RestartAction key.
        if not validate_restart_action_key(pkginfo, filename):
            retval = 1

        # Check for common mistakes in min/max OS version keys.
        os_vers_corrections = {
            "min_os": "minimum_os_version",
            "max_os": "maximum_os_version",
            "min_os_vers": "minimum_os_version",
            "max_os_vers": "maximum_os_version",
            "minimum_os": "minimum_os_version",
            "maximum_os": "maximum_os_version",
            "minimum_os_vers": "minimum_os_version",
            "maximum_os_vers": "maximum_os_version",
        }
        for os_vers_key in os_vers_corrections:
            if os_vers_key in pkginfo:
                print(
                    "{}: You used {} when you probably meant {}.".format(
                        filename, os_vers_key, os_vers_corrections[os_vers_key]
                    )
                )
                retval = 1

        # Check for rogue categories.
        if args.categories and pkginfo.get("category") not in args.categories:
            print(
                '{}: category "{}" is not in list of approved categories'.format(
                    filename, pkginfo.get("category")
                )
            )
            retval = 1

        # Check for rogue catalogs.
        if args.catalogs:
            for catalog in pkginfo.get("catalogs"):
                if catalog not in args.catalogs:
                    print(
                        '{}: catalog "{}" is not in approved list'.format(
                            filename, catalog
                        )
                    )
                    retval = 1

        # Check for pkg filenames showing signs of duplicate imports.
        if pkginfo.get("installer_item_location", "").endswith(tuple(dupe_suffixes)):
            print(
                '{}: installer item "{}" may be a duplicate import'.format(
                    filename, pkginfo.get("installer_item_location")
                )
            )
            retval = 1

        # Checking for the absence of blocking_applications for pkg installers.
        # If a pkg doesn't require blocking_applications, use empty "<array/>" in pkginfo.
        if args.require_pkg_blocking_apps and all(
            (
                "blocking_applications" not in pkginfo,
                pkginfo.get("installer_item_location", "").endswith(".pkg"),
                pkginfo.get("RestartAction") not in blocking_actions,
                not pkginfo["name"].startswith("munkitools"),
            )
        ):
            print(
                "{}: contains a pkg installer but missing a blocking applications array".format(
                    filename
                )
            )
            retval = 1

        # Ensure an icon exists for the item.
        if not any(
            (
                pkginfo.get("icon_name"),
                os.path.isfile("icons/{}.png".format(pkginfo["name"])),
                pkginfo.get("installer_type") == "apple_update_metadata",
            )
        ):
            print("{}: missing icon".format(filename))
            retval = 1

        # Ensure uninstall method is set correctly if uninstall_script exists.
        if "uninstall_script" in pkginfo:
            if pkginfo.get("uninstall_method") != "uninstall_script":
                print(
                    '{}: has uninstall script, but the uninstall method is set to "{}"'.format(
                        filename, pkginfo.get("uninstall_method")
                    )
                )
                retval = 1

        # Ensure all pkginfo scripts have a proper shebang.
        shebangs = (
            "#!/bin/bash",
            "#!/bin/sh",
            "#!/bin/zsh",
            "#!/usr/bin/osascript",
            "#!/usr/bin/perl",
            "#!/usr/bin/python",
            "#!/usr/bin/ruby",
            "#!/usr/local/munki/munki-python",
            "#!/usr/local/munki/Python.framework/Versions/Current/bin/python3",
        )
        script_types = (
            "installcheck_script",
            "uninstallcheck_script",
            "postinstall_script",
            "postuninstall_script",
            "preinstall_script",
            "preuninstall_script",
            "uninstall_script",
        )
        for script_type in script_types:
            if script_type in pkginfo:
                if all(not pkginfo[script_type].startswith(x + "\n") for x in shebangs):
                    print(
                        "{}: Has a {} that does not start with a valid shebang.".format(
                            filename, script_type
                        )
                    )
                    retval = 1

        # Ensure the items_to_copy list does not include trailing slashes.
        # Credit to @bruienne for this idea.
        # https://gist.github.com/bruienne/9baa958ec6dbe8f09d94#file-munki_fuzzinator-py-L211-L219
        if "items_to_copy" in pkginfo:
            for item_to_copy in pkginfo.get("items_to_copy"):
                if item_to_copy.get("destination_path").endswith("/"):
                    print(
                        '{}: has an items_to_copy with a trailing slash: "{}"'.format(
                            filename, item_to_copy["destination_path"]
                        )
                    )
                    retval = 1

    return retval


if __name__ == "__main__":
    exit(main())
