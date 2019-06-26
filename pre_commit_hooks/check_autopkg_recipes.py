#!/usr/bin/python
"""This hook checks AutoPkg recipes to ensure they contain required top-level
keys.

(https://github.com/autopkg/autopkg/wiki/Recipe-Format)
"""

import argparse
import plistlib
from distutils.version import LooseVersion
from xml.parsers.expat import ExpatError

from pre_commit_hooks.util import validate_pkginfo_key_types, validate_required_keys

# Processors for which a minimum version of AutoPkg is required.
PROC_MIN_VERSIONS = {
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

# Processors for which %NAME%.app should not be present in the arguments.
NO_NAME_VAR_IN_PROC_ARGS = (
    "CodeSignatureVerifier",
    "Versioner",
    "PkgPayloadUnpacker",
    "FlatPkgUnpacker",
    "FileFinder",
    "Copier",
    "AppDmgVersioner",
    "InstallFromDMG",
)


def build_argument_parser():
    """Build and return the argument parser."""

    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument(
        "--override-prefix",
        default="local.",
        help='Expected prefix for recipe override identifiers (defaults to "local").',
    )
    parser.add_argument(
        "--recipe-prefix",
        default="com.github.",
        help='Expected prefix for recipe identifiers (defaults to "com.github").',
    )
    parser.add_argument(
        "--ignore-min-vers-before",
        default="1.0.0",
        help="Ignore MinimumVersion/processor mismatches below this version of AutoPkg "
        '(defaults to "1.0.0").\nSet to 0.1.0 to warn about all '
        "MinimumVersion/processor mismatches.",
    )
    parser.add_argument("filenames", nargs="*", help="Filenames to check.")
    return parser


def main(argv=None):
    """Main process."""

    # Parse command line arguments.
    argparser = build_argument_parser()
    args = argparser.parse_args(argv)

    retval = 0
    for filename in args.filenames:
        try:
            recipe = plistlib.readPlist(filename)

        except (ExpatError, ValueError) as err:
            print("{}: plist parsing error: {}".format(filename, err))
            retval = 1
            break  # No need to continue checking this file

        # Top level keys that all AutoPkg recipes should contain.
        required_keys = ("Identifier",)
        if not validate_required_keys(recipe, filename, required_keys):
            retval = 1
            break  # No need to continue checking this file

        if args.override_prefix and "Process" not in recipe:
            override_prefix = args.override_prefix
            if not recipe["Identifier"].startswith(override_prefix):
                print(
                    '{}: override identifier does not start with "{}"'.format(
                        filename, override_prefix
                    )
                )
                retval = 1
        if args.recipe_prefix and "Process" in recipe:
            recipe_prefix = args.recipe_prefix
            if not recipe["Identifier"].startswith(recipe_prefix):
                print(
                    '{}: recipe identifier does not start with "{}"'.format(
                        filename, recipe_prefix
                    )
                )
                retval = 1

        input_key = recipe.get("Input", recipe.get("input", recipe.get("INPUT")))
        if input_key and "pkginfo" in input_key:
            if not validate_pkginfo_key_types(input_key["pkginfo"], filename):
                retval = 1

            # TODO: Additional pkginfo checks here.

        # Warn about comments that would be lost during `plutil -convert xml1`
        with open(filename, "r") as openfile:
            recipe_text = openfile.read()
            if "<!--" in recipe_text and "-->" in recipe_text:
                print(
                    "{}: WARNING: Recommend converting from <!-- --> style comments "
                    "to a Comment key where needed.".format(filename)
                )

        # Processor checks.
        if "Process" in recipe:

            # Ensure all items in Process array have a "Processor" specified.
            missing_processor_keys = [
                x for x in recipe["Process"] if "Processor" not in x
            ]
            if missing_processor_keys:
                for missing_proc in missing_processor_keys:
                    print(
                        '{}: Item in processor array is missing "Processor" key: {}'.format(
                            filename, missing_proc
                        )
                    )
                retval = 1

            # Ensure MinimumVersion is set appropriately for the processors used.
            if "MinimumVersion" in recipe:
                for proc in [
                    x
                    for x in PROC_MIN_VERSIONS
                    if LooseVersion(PROC_MIN_VERSIONS[x])
                    >= LooseVersion(args.ignore_min_vers_before)
                ]:
                    if proc in [x["Processor"] for x in recipe["Process"]]:
                        if LooseVersion(recipe["MinimumVersion"]) < LooseVersion(
                            PROC_MIN_VERSIONS[proc]
                        ):
                            print(
                                "{}: {} processor requires minimum AutoPkg "
                                "version {}".format(
                                    filename, proc, PROC_MIN_VERSIONS[proc]
                                )
                            )
                            retval = 1

            # Ensure %NAME% is not used in app paths that should be hard coded.
            for process in recipe["Process"]:
                if process["Processor"] in NO_NAME_VAR_IN_PROC_ARGS:
                    for _, argvalue in process["Arguments"].items():
                        if isinstance(argvalue, str) and "%NAME%.app" in argvalue:
                            print(
                                "{}: Use actual app name instead of %NAME%.app in {} "
                                "processor argument.".format(
                                    filename, process["Processor"]
                                )
                            )
                            retval = 1

    return retval


if __name__ == "__main__":
    exit(main())
