#!/usr/bin/python
"""This hook checks Munki pkginfo files to ensure they are valid."""

import argparse
import os
import plistlib
from pathlib import Path
from xml.parsers.expat import ExpatError

from pre_commit_hooks.util import (
    detect_deprecated_keys,
    detect_typoed_keys,
    validate_pkginfo_key_types,
    validate_required_keys,
    validate_restart_action_key,
    validate_shebangs,
    validate_uninstall_method,
)


def build_argument_parser():
    """Build and return the argument parser."""

    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument("--categories", nargs="+", help="List of approved categories.")
    parser.add_argument("--catalogs", nargs="+", help="List of approved catalogs.")
    default_req_keys = ["description", "name", "version"]
    parser.add_argument(
        "--required-keys",
        nargs="+",
        default=default_req_keys,
        help=f"List of required top-level keys. Defaults to: {default_req_keys}",
    )
    parser.add_argument(
        "--require-pkg-blocking-apps",
        action="store_true",
        help="Require a blocking_applications array for pkg installers.",
    )
    parser.add_argument("filenames", nargs="*", help="Filenames to check.")
    parser.add_argument(
        "--munki-repo", default=".", help="path to local munki repo. Defaults to '.'"
    )
    parser.add_argument(
        "--warn-on-missing-icons",
        help="If added, this will only warn on missing icons.",
        action="store_true",
        default=False,
    )
    parser.add_argument(
        "--warn-on-missing-installer-items",
        help="If added, this will only warn on missing installer items.",
        action="store_true",
        default=False,
    )
    parser.add_argument(
        "--warn-on-duplicate-imports",
        help="If added, this will only warn if pkginfo/pkg files end with a __1 suffix.",
        action="store_true",
        default=False,
    )
    parser.add_argument(
        "--valid-shebangs",
        nargs="+",
        default=[],
        help="Add other valid shebangs for your environment",
    )
    return parser


def _check_case_sensitive_path(path):
    """Check whether a path exists, and on case-sensitive filesystems check
    that there is no case conflict."""
    # Return immediately if the file does not exist
    if not os.path.exists(path):
        return False

    p = Path(path)
    while True:
        # At root, p == p.parent --> break loop and return True
        if p == p.parent:
            return True
        # If string representation of path is not in parent directory, return False
        if str(p) not in list(map(str, p.parent.iterdir())):
            return False
        p = p.parent


def main(argv=None):
    """Main process."""

    # Typical extensions for installer packages.
    pkg_exts = ("pkg", "dmg")
    dupe_suffixes = [f"__{i}.{ext}" for ext in pkg_exts for i in range(1, 9)]

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
            print(f"{filename}: plist parsing error: {err}")
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

        # Validate uninstall method.
        if not validate_uninstall_method(pkginfo, filename):
            retval = 1

        # Check for deprecated pkginfo keys.
        if not detect_deprecated_keys(pkginfo, filename):
            retval = 1

        # Check for common mistakes in key names.
        if not detect_typoed_keys(pkginfo, filename):
            retval = 1

        # Check for rogue categories.
        if args.categories and pkginfo.get("category") not in args.categories:
            print(
                f"{filename}: category \"{pkginfo.get('category')}\" is not in list of approved categories"
            )
            retval = 1

        # Check for rogue catalogs.
        if args.catalogs:
            for catalog in pkginfo.get("catalogs"):
                if catalog not in args.catalogs:
                    print(f'{filename}: catalog "{catalog}" is not in approved list')
                    retval = 1

        # Check for missing or case-conflicted installer items
        if not _check_case_sensitive_path(
            os.path.join(
                args.munki_repo, "pkgs", pkginfo.get("installer_item_location", "")
            )
        ):
            msg = "installer item does not exist or path is not case sensitive"
            if args.warn_on_missing_installer_items:
                print(f"{filename}: WARNING: {msg}")
            else:
                print(f"{filename}: {msg}")
                retval = 1

        # Check for pkg filenames showing signs of duplicate imports.
        if pkginfo.get("installer_item_location", "").endswith(tuple(dupe_suffixes)):
            installer_item_location = pkginfo["installer_item_location"]
            msg = (
                f"installer item '{installer_item_location}' may be a duplicate import"
            )
            if args.warn_on_missing_icons:
                print(f"{filename}: WARNING: {msg}")
            else:
                print(f"{filename}: {msg}")
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
                f"{filename}: contains a pkg installer but missing a blocking applications array"
            )
            retval = 1

        # Ensure an icon exists for the item.
        if not any(
            (
                pkginfo.get("icon_name"),
                os.path.isfile(
                    os.path.join(args.munki_repo, f"icons/{pkginfo['name']}.png")
                ),
                pkginfo.get("installer_type") == "apple_update_metadata",
            )
        ):
            msg = "missing icon"
            if args.warn_on_missing_icons:
                print(f"{filename}: WARNING: {msg}")
            else:
                print(f"{filename}: {msg}")
                retval = 1

        # Ensure all pkginfo scripts have a proper shebang.
        script_types = (
            "installcheck_script",
            "uninstallcheck_script",
            "postinstall_script",
            "postuninstall_script",
            "preinstall_script",
            "preuninstall_script",
            "uninstall_script",
        )
        for s_type in script_types:
            if s_type in pkginfo:
                if not validate_shebangs(
                    pkginfo[s_type], filename, args.valid_shebangs
                ):
                    print(f"{filename}: {s_type} does not start with a valid shebang")
                    retval = 1

        # Ensure the items_to_copy list does not include trailing slashes.
        # Credit to @bruienne for this idea.
        # https://gist.github.com/bruienne/9baa958ec6dbe8f09d94#file-munki_fuzzinator-py-L211-L219
        if "items_to_copy" in pkginfo:
            for item_to_copy in pkginfo.get("items_to_copy"):
                if item_to_copy.get("destination_path").endswith("/"):
                    print(
                        f'{filename}: has an items_to_copy with a trailing slash: "{item_to_copy["destination_path"]}"'
                    )
                    retval = 1

    return retval


if __name__ == "__main__":
    exit(main())
