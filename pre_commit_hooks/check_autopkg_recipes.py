#!/usr/bin/python
"""This hook checks AutoPkg recipes to ensure they contain required top-level
keys.

(https://github.com/autopkg/autopkg/wiki/Recipe-Format)
"""

import argparse
import plistlib
from xml.parsers.expat import ExpatError
from distutils.version import LooseVersion

from pre_commit_hooks.util import validate_pkginfo_key_types


def build_argument_parser():
    """Build and return the argument parser."""

    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument(
        "--override-prefix",
        default="local.",
        help='Expected prefix for recipe override identifiers. (defaults to "local")',
    )
    parser.add_argument(
        "--recipe-prefix",
        default="com.github.",
        help='Expected prefix for recipe identifiers. (defaults to "com.github")',
    )
    parser.add_argument("filenames", nargs="*", help="Filenames to check.")
    return parser


def main(argv=None):
    """Main process."""

    # Top level keys that all AutoPkg recipes should contain.
    required_keys = ("Identifier", "Input")

    # Parse command line arguments.
    argparser = build_argument_parser()
    args = argparser.parse_args(argv)

    retval = 0
    for filename in args.filenames:
        try:
            recipe = plistlib.readPlist(filename)
            for req_key in required_keys:
                if req_key not in recipe:
                    print("{}: missing required key {}".format(filename, req_key))
                    retval = 1
                    break  # No need to continue checking this file

        except (ExpatError, ValueError) as err:
            print("{}: plist parsing error: {}".format(filename, err))
            retval = 1
            break  # No need to continue checking this file

        if args.override_prefix and "Process" not in recipe:
            override_prefix = args.override_prefix
            if not recipe.get("Identifier", "").startswith(override_prefix):
                print(
                    '{}: override identifier does not start with "{}"'.format(
                        filename, override_prefix
                    )
                )
                retval = 1
        if args.recipe_prefix and "Process" in recipe:
            recipe_prefix = args.recipe_prefix
            if not recipe.get("Identifier", "").startswith(recipe_prefix):
                print(
                    '{}: recipe identifier does not start with "{}"'.format(
                        filename, recipe_prefix
                    )
                )
                retval = 1

        input = recipe.get("Input", recipe.get("input", recipe.get("INPUT")))
        if input and "pkginfo" in input:
            if not validate_pkginfo_key_types(input["pkginfo"], filename):
                retval = 1

        # Ensure MinimumVersion is set appropriately for the processors used.
        processor_min_versions = {
            "AppPkgCreator": "1.0.0",
            "BrewCaskInfoProvider": "0.2.5",
            "CodeSignatureVerifier": "0.3.1",
            "CURLDownloader": "0.5.1",
            "CURLTextSearcher": "0.5.1",
            "DeprecationWarning": "1.1.0",
            "EndOfCheckPhase": "0.1.0",
            "FileFinder": "0.2.3",
            "FileMover": "0.2.9",
            "FlatPkgPacker": "0.2.4",
            "FlatPkgUnpacker": "0.1.0",
            "GitHubReleasesInfoProvider": "0.5.0",
            "Installer": "0.4.0",
            "InstallFromDMG": "0.4.0",
            "MunkiCatalogBuilder": "0.1.0",
            "MunkiImporter": "0.1.0",
            "MunkiInstallsItemsCreator": "0.1.0",
            "MunkiPkginfoMerger": "0.1.0",
            "MunkiSetDefaultCatalog": "0.4.2",
            "PackageRequired": "0.5.1",
            "PathDeleter": "0.1.0",
            "PkgCopier": "0.1.0",
            "PkgExtractor": "0.1.0",
            "PkgPayloadUnpacker": "0.1.0",
            "PlistEditor": "0.1.0",
            "PlistReader": "0.2.5",
            "SparkleUpdateInfoProvider": "0.1.0",
            "StopProcessingIf": "0.1.0",
            "Symlinker": "0.1.0",
            "Unarchiver": "0.1.0",
            "URLTextSearcher": "0.2.9",
            "Versioner": "0.1.0",
        }
        if "Process" in recipe and "MinimumVersion" in recipe:
            for proc in processor_min_versions:
                if proc in [x["Processor"] for x in recipe["Process"]]:
                    if LooseVersion(recipe["MinimumVersion"]) < LooseVersion(
                        processor_min_versions[proc]
                    ):
                        print(
                            "{}: {} processor requires minimum AutoPkg version {}".format(
                                filename, proc, processor_min_versions[proc]
                            )
                        )
                        retval = 1

    return retval


if __name__ == "__main__":
    exit(main())
