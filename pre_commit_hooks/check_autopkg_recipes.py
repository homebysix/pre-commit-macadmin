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
        "MinimumVersion/processor mismatches.\nDefaults to 0.1.0 if --strict is used.",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        default=False,
        help="Apply strictest set of rules when evaluating AutoPkg recipes, including "
        "adherence to recipe type conventions, flagging all MinimumVersion/processor "
        "mismatches, and forbidding <!-- --> comments. Very opinionated.",
    )
    parser.add_argument("filenames", nargs="*", help="Filenames to check.")
    return parser


def validate_processor_keys(process, filename):
    """Ensure all items in Process array have a "Processor" specified."""

    passed = True
    missing_processor_keys = [x for x in process if "Processor" not in x]
    if missing_processor_keys:
        for missing_proc in missing_processor_keys:
            print(
                '{}: Item in processor array is missing "Processor" key:\n{}'.format(
                    filename, missing_proc
                )
            )
        passed = False

    return passed


def validate_endofcheckphase(process, filename):
    """Ensure EndOfCheckPhase comes after a downloader."""

    passed = True
    downloader_idx = next(
        (
            idx
            for (idx, x) in enumerate(process)
            if x.get("Processor") in ("URLDownloader", "CURLDownloader")
        ),
        None,
    )
    endofcheck_idx = next(
        (
            idx
            for (idx, x) in enumerate(process)
            if x.get("Processor") == "EndOfCheckPhase"
        ),
        None,
    )
    if (
        downloader_idx is not None
        and endofcheck_idx is not None
        and endofcheck_idx < downloader_idx
    ):
        print(
            "{}: EndOfCheckPhase typically goes after a download processor, "
            "not before.".format(filename)
        )
        passed = False

    return passed


def validate_minimumversion(process, min_vers, ignore_min_vers_before, filename):
    """Ensure MinimumVersion is set appropriately for the processors used."""

    # Processors for which a minimum version of AutoPkg is required.
    proc_min_versions = {
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

    passed = True
    for proc in [
        x
        for x in proc_min_versions
        if LooseVersion(proc_min_versions[x]) >= LooseVersion(ignore_min_vers_before)
    ]:
        if proc in [x.get("Processor") for x in process]:
            if LooseVersion(min_vers) < LooseVersion(proc_min_versions[proc]):
                print(
                    "{}: {} processor requires minimum AutoPkg "
                    "version {}".format(filename, proc, proc_min_versions[proc])
                )
                passed = False

    return passed


def validate_no_var_in_app_path(process, filename):
    """Ensure %NAME% is not used in app paths that should be hard coded."""

    # Processors for which %NAME%.app should not be present in the arguments.
    no_name_var_in_proc_args = (
        "CodeSignatureVerifier",
        "Versioner",
        "PkgPayloadUnpacker",
        "FlatPkgUnpacker",
        "FileFinder",
        "Copier",
        "AppDmgVersioner",
        "InstallFromDMG",
    )

    passed = True
    for proc in process:
        if proc.get("Processor") in no_name_var_in_proc_args and "Arguments" in proc:
            for _, argvalue in proc["Arguments"].items():
                if isinstance(argvalue, str) and "%NAME%.app" in argvalue:
                    print(
                        "{}: Use actual app name instead of %NAME%.app in {} "
                        "processor argument.".format(filename, proc.get("Processor"))
                    )
                    passed = False

    return passed


def validate_proc_type_conventions(process, filename):
    """Ensure that processors used align with recipe type conventions."""

    # For each processor type, this is the list of processors that
    # we only expect to see in that type.
    proc_type_conventions = {
        "download": [
            "SparkleUpdateInfoProvider",
            "GitHubReleasesInfoProvider",
            "URLDownloader",
            "CURLDownloader",
            "EndOfCheckPhase",
        ],
        "munki": [
            "MunkiInstallsItemsCreator",
            "MunkiPkginfoMerger",
            "MunkiCatalogBuilder",
            "MunkiSetDefaultCatalog",
            "MunkiImporter",
        ],
        "pkg": ["AppPkgCreator", "PkgCreator"],
        "install": ["InstallFromDMG", "Installer"],
        "jss": ["JSSImporter"],
        "filewave": ["FileWaveImporter"],
    }

    passed = True
    processors = [x["Processor"] for x in process]
    for recipe_type in proc_type_conventions:
        type_hint = ".{}.".format(recipe_type)
        if type_hint not in filename:
            for processor in processors:
                if processor in proc_type_conventions[recipe_type]:
                    print(
                        "{}: Processor {} is not conventional for this "
                        "recipe type.".format(filename, processor)
                    )
                    passed = False

    return passed


def validate_required_proc_for_types(process, filename):
    """Ensure that certain recipe types always have specific processors."""

    # For each recipe type, this is the list of processors that
    # MUST exist in that type. Uses "OR" logic, not "AND."
    required_proc_for_type = {
        "download": ["EndOfCheckPhase"],
        "munki": ["MunkiImporter"],
        "pkg": ["AppPkgCreator", "PkgCreator"],
        "install": ["InstallFromDMG", "Installer"],
        "jss": ["JSSImporter"],
        "filewave": ["FileWaveImporter"],
    }

    passed = True
    processors = [x["Processor"] for x in process]
    for recipe_type in required_proc_for_type:
        req_procs = required_proc_for_type[recipe_type]
        type_hint = ".{}.".format(recipe_type)
        if type_hint in filename:
            if recipe_type == "pkg" and processors == []:
                # OK for pkg recipes to have an empty process list, as long as
                # their parent is a download recipe that produces a pkg.
                # TODO: Validate parent is a download recipe.
                break
            if not any([x in processors for x in req_procs]):
                if len(req_procs) == 1:
                    print(
                        "{}: Recipe type {} should contain processor "
                        "{}.".format(filename, recipe_type, req_procs[0])
                    )
                else:
                    print(
                        "{}: Recipe type {} should contain one of these "
                        "processors: {}.".format(filename, recipe_type, req_procs)
                    )
                passed = False

    return passed


def main(argv=None):
    """Main process."""

    # Parse command line arguments.
    argparser = build_argument_parser()
    args = argparser.parse_args(argv)
    if args.strict:
        args.ignore_min_vers_before = "0.1.0"

    retval = 0
    for filename in args.filenames:
        try:
            recipe = plistlib.readPlist(filename)

        except (ExpatError, ValueError) as err:
            print("{}: plist parsing error: {}".format(filename, err))
            retval = 1
            break  # No need to continue checking this file

        # Top level keys that all AutoPkg recipes should contain.
        required_keys = ["Identifier"]
        if not validate_required_keys(recipe, filename, required_keys):
            retval = 1
            break  # No need to continue checking this file

        # Warn if the recipe/override identifier does not start with the expected prefix.
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
                if args.strict:
                    print(
                        "{}: Convert from <!-- --> style comments "
                        "to a Comment key.".format(filename)
                    )
                    retval = 1
                else:
                    print(
                        "{}: WARNING: Recommend converting from <!-- --> style comments "
                        "to a Comment key.".format(filename)
                    )

        # Processor checks.
        if "Process" in recipe:
            process = recipe["Process"]

            if not validate_processor_keys(process, filename):
                retval = 1

            if not validate_endofcheckphase(process, filename):
                retval = 1

            if not validate_no_var_in_app_path(process, filename):
                retval = 1

            min_vers = recipe.get("MinimumVersion")
            if min_vers and not validate_minimumversion(
                process, min_vers, args.ignore_min_vers_before, filename
            ):
                retval = 1

            if args.strict:
                if not validate_proc_type_conventions(process, filename):
                    retval = 1

                if not validate_required_proc_for_types(process, filename):
                    retval = 1

    return retval


if __name__ == "__main__":
    exit(main())
