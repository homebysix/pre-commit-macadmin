#!/usr/bin/python
"""This hook checks Munki pkginfo files to ensure they are valid."""

import argparse
import os
import plistlib
from xml.parsers.expat import ExpatError

from pre_commit_hooks.util import validate_pkginfo_key_types


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
            pkginfo = plistlib.readPlist(filename)
        except (ExpatError, ValueError) as err:
            print("{}: plist parsing error: {}".format(filename, err))
            retval = 1

        # Check for presence of required pkginfo keys.
        if args.required_keys:
            for req_key in args.required_keys:
                if not pkginfo.get(req_key):
                    print('{}: missing required key "{}"'.format(filename, req_key))
                    retval = 1
                    break  # No need to continue checking this file

        # Ensure pkginfo keys have expected types.
        retval = validate_pkginfo_key_types(pkginfo, filename)

        # Check for rogue categories.
        if args.categories and pkginfo.get("category") not in args.categories:
            print(
                '{}: category "{}" is not in approved list'.format(
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
        if all(
            (
                "blocking_applications" not in pkginfo,
                pkginfo.get("installer_item_location", "").endswith(".pkg"),
                pkginfo.get("RestartAction") not in blocking_actions,
                not pkginfo["name"].startswith("munkitools"),
            )
        ):
            print(
                "{}: contains a pkg installer but has no blocking applications".format(
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

    return retval


if __name__ == "__main__":
    exit(main())
