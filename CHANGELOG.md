# pre-commit-macadmin change log

All notable changes to this project will be documented in this file. This project adheres to [Semantic Versioning](http://semver.org/).

<!-- markdownlint-configure-file
{
  "no-duplicate-heading": {
    "siblings_only": true
  }
}
-->

## [Unreleased]

Nothing yet.

## [1.21.0] - 2025-09-21

### Added

- `check-munki-pkgsinfo` now detects the incorrect key `condition` and suggests using `installable_condition` instead.

### Changed

- Renamed internal package from `pre_commit_hooks` to `pre_commit_macadmin_hooks` to resolve namespace collision with the official `pre_commit_hooks` [package](https://github.com/pre-commit/pre-commit-hooks). (#78)

## [1.20.0] - 2025-08-09

### Added

- `check-autopkg-recipes` and `check-munki-pkgsinfo` now validates that `supported_architectures` values are set appropriately.
- In anticipation of Munki 7, `check-munki-pkgsinfo` validates that `version_script` is a string starting with a script shebang.
- `check-munki-pkgsinfo` now checks for specific deprecated `installer_type` and `uninstall_method` values, most of which are detailed [here](https://github.com/munki/munki/wiki/Deprecation-Notes).
- Added new FindAndReplace core processor version requirements for AutoPkg recipes.

### Changed

- Improvements to `check-preference-manifests` hook. (#91, thanks to @relgit)
- `check-autopkg-recipes` ignores `supported_architectures` values within Munki pkginfo dictionaries that appear to be AutoPkg recipe substitution variables (e.g. `%ARCH%`).

## [1.19.0] - 2025-01-16

### Added

- Added `--warn-on-missing-installer-items` flag that makes missing Munki install/uninstall items a warning instead of a failure. (#86, thanks to @haircut)
- Apply the same checks to `uninstaller_item_location` that were previously applied to `installer_item_location`.
- `check-autopkg-recipes` requires Munki recipe `pkginfo` dicts to contain at least `name` and `description`.
- `check-autopkg-recipes` now validates that `uninstall_method` and `uninstall_script` are set appropriately in Munki recipes.

### Changed

- `check-autopkg-recipes` includes jamf-upload as an AutoPkg recipe type, and updated processors included in jamf/jamf-upload recipe convention.
- `check-munki-pkgsinfo` requires a `version` key in addition to `name` and `description`.

### Fixed

- Bug fix in `check-munkiadmin-scripts` that prevented script names from processing correctly.
- Bug fix in `check-munki-pkgsinfo` that prevented `--warn-on-duplicate-imports` flag from working correctly.

## [1.18.0] - 2025-01-04

### Added

- `check-munki-pkgsinfo` now produces an error if `uninstall_method` is set to `uninstall_script` but no uninstall script is present in the pkginfo.
- `check-munki-pkgsinfo` now checks for deprecated pkginfo keys.
- `check-munki-pkgsinfo` now includes checks for many possible pkginfo key typos, not just `minimum_os_version` and `maximum_os_version`. Suggestions welcome if you think of more.
- `check-munkiadmin-scripts` now checks whether scripts are named correctly, not just executable.

## [1.17.0] - 2024-12-22

### Added

- New `--warn-on-duplicate-imports` flag for use with Munki pkginfo checks, for Munki administrators who don't care about multiple potential versions of the same pkginfo/pkg in the repository (perhaps because of differing `supported_architectures` or other keys).

    When this is specified, the pre-commit hook will warn when files with `__1` (and similar) suffixes are seen in the pkgsinfo/pkgs folders. This will enbale pre-commit hooks to pass, as long as there are no other errors. Omitting the `--warn-on-duplicate-imports` flag will continue generating an error and failing the hooks, as was the previous behavior.

- Include `SignToolVerifier` and `URLDownloaderPython` AutoPkg processors when suggesting minimum versions.
- Updated AutoPkg recipe type convention checking to include new `JamfUpload` processors as well as `URLDownloaderPython` and `MunkiInfoCreator`.
- Added a suggestion to use Rich Trouton's [VariablePlaceholder](https://derflounder.wordpress.com/2024/08/16/setting-custom-variables-in-autopkg-using-the-variableplaceholder-processor/) processor for setting arbitrary environment variables instead of supplying unexpected arguments to existing processors.

### Fixed

- Fixed FileWaveImporter processor detection.

## [1.16.2] - 2024-06-10

### Fixed

- Fixed two bugs in shebang validation that would result in ModuleNotFoundError when running check-munki-pkgsinfo hook.

### Removed

- Dropped Python 2 string instance validation. No further support will be provided for Python 2.

### Changed

- Added PyUpgrade hook to this repo's own pre-commit linting, in order to ensure modern Python syntax.
- Don't specify `"r"` mode when using `open()`, as this is the default behavior.

## [1.16.1] - 2024-06-08

### Added

- New `format-xml-plist` hook to auto-format XML property list (plist) files to use tabs instead of spaces, and will alphabetically sort keys. (#79, thanks to n8felton)
- New `--valid-shebangs` parameter to specify additional custom shebangs in use for your environment. Works with the `check-munki-pkgsinfo`, `check-jamf-scripts`, `check-jamf-extension-attributes`, `check-outset-scripts`, and `check-munkiadmin-scripts` hooks. (#75, thanks to @kbrewersq)
- Checks to ensure the MinimumVersion key in AutoPkg recipes is a string. (If quotes are omitted in yaml-formatted recipes, this key could be interpreted as a float.)

### Removed

- No longer warn when using AutoPkg MinimumVersion greater than 2.0.
- Python 2 support deprecated and will be removed in the future.

### Changed

- Hook output rewritten to use f-strings instead of `.format()`.

## [1.15.0] - 2024-02-11

### Added

- Now validates that all XML `<result>` tags are closed in Jamf extension attributes. (#76, thanks to @WardsParadox)

### Fixed

- Fixed a bug in the `munki-makecatalogs` hook (#72, thanks to @kbrewersq).
- Added optional `--munki-repo` parameter to `check-munki-pkgsinfo` and `munki-makecatalogs` hooks, in order to specify a path to your Munki repo. Useful for situations where the Munki repo is a subdirectory of the Git repo itself. (#73 and #74, thanks to @kbrewersq)

## [1.14.1] - 2023-11-20

### Fixed

- Fixed a bug that would cause a Python traceback when checking Munki repos that use `nopkg` type items.

## [1.14.0] - 2023-11-19

### Added

- `check-preference-manifests` hook now outputs more specific error message if `pfm_documentation_url` is empty. (#67, thanks to @relgit)
- `check-munki-pkgsinfo` hook now detects path mismatches on case-sensitive filesystems. (#66, thanks to @AaronBurchfield)

## [1.13.0] - 2023-11-18

### Changed

- Now uses `packaging.version.Version` instead of `distutils.version.LooseVersion` for AutoPkg version comparisons. This may cause unexpected behavior if unusual versions are used in `MinimumVersion` keys.
- Updated `yaml.safe_load()` to `YAML(typ='safe')`.

## [1.12.4] - 2023-02-26

### Added

- Added compatibility checks for MunkiOptionalReceiptEditor processor, included in AutoPkg 2.7+.
- Added a `--require-pkg-blocking-apps` argument for the `check-munki-pkgsinfo` hook. If specified, tests will fail for any pkg installer that does not have a `blocking_applications` array (even an empty one). This change maintains the alignment with Munki's design established in 1.12.3 while allowing Munki repo admins flexibility to be stricter in their own environments.

### Changed

- Improved compatibility with Munki repos where the pkgsinfo folder is not at the root level. (#63, thanks to @kbrewersq)

## [1.12.3] - 2022-04-09

### Changed

- Changed check-munki-pkgsinfo to WARN on the absence of the `blocking_applications` array for installers in pkg format, rather than to fail the pre-commit test. This better aligns with Munki's own design, which does not require `blocking_applications`.

### Fixed

- Resolved an uncaught exception if the git config email is unset. (#58)

## [1.12.2] - 2022-02-27

### Changed

- Adjusted preference manifest checks to require `pfm_name` for every preference key except immediate descendants of keys whose `pfm_type` is `array` (#54).
- Improved preference manifest output to more accurately specify which key or subkey is failing `pfm_name` or `pfm_type` checks.
- Continued development work on a hook that checks Jamf JSON schema manifests.

## [1.12.1] - 2021-12-22

### Changed

- Minor adjustments to `check-preference-manifests` hook.

## [1.12.0] - 2021-12-19

### Added

- New `check-preference-manifests` hook for checking Apple preference manifests like those used by ProfileCreator and iMazing Profile Editor [manifests](https://github.com/ProfileCreator/ProfileManifests).
- Check for the [recommended order](https://youtu.be/srz4U9RHliQ?list=PLlxHm_Px-Ie1EIRlDHG2lW5H7c2UYvops&t=1010) of JamfUploader processors.

## [1.11.0] - 2021-11-20

### Added

- Added processor type conventions for [JamfUploader](https://grahamrpugh.com/2020/12/14/introducing-jamf-upload.html) (`.jamf`), [PkgSigner](https://derflounder.wordpress.com/2021/07/30/signing-autopkg-built-packages-using-a-sign-recipe/) (`.sign`), and [GPGSignatureVerifier](https://github.com/autopkg/gerardkok-recipes/blob/master/SharedProcessors/GPGSignatureVerifier.py) (`.verify`) families of recipes.
- `BrewCaskInfoProvider` has been added to the list of deprecated AutoPkg processors.
- More output when `check-git-config-email` fails.

## [1.10.1] - 2021-02-21

### Added

- In anticipation of AutoPkg 2.3, now supports checking YAML recipes (must have extension `.recipe.yaml`).
- In anticipation of AutoPkg 2.3, supports additional AutoPkg plist extension `.recipe.plist`.
- Supports JSON AutoPkg recipes (must have extension `.recipe.json`). NOTE: AutoPkg itself does not yet support JSON recipes.
- Built placeholder for checking for unused AutoPkg recipe input variables in the future. Check is disabled for now.

### Fixed

- Fixed a bug preventing display of AutoPkg recipe path and identifier if duplicate identifier is found in the repo.

## [1.9.0] - 2021-01-18

### Added

- Added check for any unexpected processor arguments in any AutoPkg processor.

### Removed

- CodeSignatureVerifier processor argument verification (added in v1.8.2) has been replaced by the above.

## [1.8.2] - 2021-01-18

### Added

- Added check for unexpected processor arguments in CodeSignatureVerifier.

### Changed

- Renamed default branch to `main`.

## [1.8.1] - 2020-12-08

### Removed

- Removed warning about setting MinimumVersion of AutoPkg recipes to 2.0+.
- Reverted 1.4 minimum version requirement for processors that use URLGetter (introduced in 1.7.0).

## [1.8.0] - 2020-10-08

### Changed

- Replaced `plistlib.readPlist()` with `plistlib.load()`

## [1.7.0] - 2020-10-06

### Added

- Added pre-commit-macadmin change log (this file)
- Ensure no superclass processors (e.g. URLGetter) are used, as these are intended to be referred to by other processors rather than directly used in recipes
- Warn if setting a MinimumVersion greater than or equal to 2 in AutoPkg recipes, because some administrators may be running 1.4.1 and waiting for processor authors to add Python 3 compatibility
- Validate `minimum_os_version` and `maximum_os_version` keys in Munki pkginfo files

### Changed

- Set MinimumVersion needed for [C]URL* processors to 1.4, to ensure utilization of URLGetter
- Updated valid Munki script shebangs to include Munki embedded Python symlink and path

## [1.6.2] - 2020-01-20

### Fixed

- Added missing sys module for Python version determination

## [1.6.1] - 2019-12-26

### Fixed

- Convert subprocess output to string

## [1.6.0] - 2019-12-26

### Added

- Validate possible values of RestartAction key in Munki pkginfo
- New hook to check Git user email configuration (`git config user.email`)

## [1.5.2] - 2019-11-26

### Fixed

- Removed redundant EndOfCheckPhase check
- Added URLGetter minimum version (although we should never need this since URLGetter is not meant to be called directly)

## [1.5.1] - 2019-09-21

### Added

- Checking for downloader processors without EndOfCheckPhase

## [1.5.0] - 2019-09-17

### Added

- Warn if using deprecated AutoPkg processors (only one exists now: CURLDownloader)
- Allow specifying multiple acceptable recipe prefixes

### Fixed

- Updated minimum AutoPkg versions required for processors to only include significant digits for LooseVersion comparison

## [1.4.0] - 2019-08-22

### Added

- Detect and warn on AutoPkg recipe identifier duplication
- Warn if any Munki pkginfo script is missing a shebang

## [1.3.0] - 2019-07-03

### Added

- `--strict` mode for check-autopkg-recipes hook, along with numerous conventions that it can validate
- Catch identifier loops, where recipe and its parent have the same identifier

### Fixed

- Better handling of unicode
- Fixed warning output when recipe list is invalid
- Fixed shared FileWaveImporter processor identifier

### Changed

- Handle recipe lists that have prefixes
- Allow pkg recipes with no process (stubs for software already in pkg format at time of download)

## [1.2.1] - 2019-06-28

### Added

- Better parsing of MunkiPkg build-info files, and validation of keys
- Better handle processors with missing Processor keys
- Warn if MunkiPkg project target disk is not the startup disk
- Validate required keys in MunkiPkg build-info files
- Validate bundle identifier in MunkiPkg build-info files

## [1.2.0] - 2019-06-27

### Added

- Checking AutoPkg recipe processors for missing Processor key
- Validation of EndOfCheckPhase placement within download recipes

### Changed

- Created shared function for checking required keys for pkginfo files and AutoPkg recipes
- No longer requiring an Input key for AutoPkg recipes

## [1.1.4] - 2019-06-24

### Changed

- Skip processor checks for AutoPkg recipes without a Process

## [1.1.3] - 2019-06-24

### Added

- Added `--ignore-min-vers-before` argument to check-autopkg-recipes hook
- Added checking for `%NAME%.app` in check-autopkg-recipes hook

## [1.1.2] - 2019-06-22

### Added

- Added validation of AutoPkg recipe MinimumVersion in check-autopkg-recipes hook

### Changed

- Fail early and stop processing files that don't parse

## [1.1.1] - 2019-06-13

### Fixed

- Fixed issue that returned wrong pass/fail result for check-munki-pkgsinfo and check-autopkg-recipes hooks

## [1.1.0] - 2019-06-13

### Added

- Added a note about combining list arguments in yaml config
- Added note about multi-line list args
- Ensure no trailing slashes on items_to_copy in check-munki-pkgsinfo

### Changed

- Specified which yaml loader to use
- Removed zip as an package extension

### Fixed

- Fixed issue that caused incorrect pass/fail for check-munki-pkgsinfo and check-autopkg-recipes hooks

## [1.0.5] - 2019-03-15

### Added

- Added args documentation to read me

## [1.0.4] - 2019-03-14

### Added

- Added check for approved catalogs

## [1.0.3] - 2019-03-13

### Fixed

- Fixed variable capitalization

## [1.0.2] - 2019-03-13

### Added

- Enabled basic type checking for pkginfo dicts

### Changed

- Adjusted required keys in check-munki-pkgsinfo to include name and description by default
- Temporarily skipping top level plist type (dict) checking

## [1.0.1] - 2019-03-03

### Added

- Added forbid-autopkg-trust-info hook
- Added check for recipe prefix enforcement

### Fixed

- Fixed bug in check-autopkg-recipes hook

## 1.0.0 - 2019-03-01

- Initial release

[Unreleased]: https://github.com/homebysix/pre-commit-macadmin/compare/v1.21.0...HEAD
[1.21.0]: https://github.com/homebysix/pre-commit-macadmin/compare/v1.20.0...v1.21.0
[1.20.0]: https://github.com/homebysix/pre-commit-macadmin/compare/v1.19.0...v1.20.0
[1.19.0]: https://github.com/homebysix/pre-commit-macadmin/compare/v1.18.0...v1.19.0
[1.18.0]: https://github.com/homebysix/pre-commit-macadmin/compare/v1.17.0...v1.18.0
[1.17.0]: https://github.com/homebysix/pre-commit-macadmin/compare/v1.16.2...v1.17.0
[1.16.2]: https://github.com/homebysix/pre-commit-macadmin/compare/v1.16.1...v1.16.2
[1.16.1]: https://github.com/homebysix/pre-commit-macadmin/compare/v1.15.0...v1.16.1
[1.15.0]: https://github.com/homebysix/pre-commit-macadmin/compare/v1.14.1...v1.15.0
[1.14.1]: https://github.com/homebysix/pre-commit-macadmin/compare/v1.14.0...v1.14.1
[1.14.0]: https://github.com/homebysix/pre-commit-macadmin/compare/v1.13.0...v1.14.0
[1.13.0]: https://github.com/homebysix/pre-commit-macadmin/compare/v1.12.4...v1.13.0
[1.12.4]: https://github.com/homebysix/pre-commit-macadmin/compare/v1.12.3...v1.12.4
[1.12.3]: https://github.com/homebysix/pre-commit-macadmin/compare/v1.12.2...v1.12.3
[1.12.2]: https://github.com/homebysix/pre-commit-macadmin/compare/v1.12.1...v1.12.2
[1.12.1]: https://github.com/homebysix/pre-commit-macadmin/compare/v1.12.0...v1.12.1
[1.12.0]: https://github.com/homebysix/pre-commit-macadmin/compare/v1.11.0...v1.12.0
[1.11.0]: https://github.com/homebysix/pre-commit-macadmin/compare/v1.10.1...v1.11.0
[1.10.1]: https://github.com/homebysix/pre-commit-macadmin/compare/v1.9.0...v1.10.1
[1.9.0]: https://github.com/homebysix/pre-commit-macadmin/compare/v1.8.2...v1.9.0
[1.8.2]: https://github.com/homebysix/pre-commit-macadmin/compare/v1.8.1...v1.8.2
[1.8.1]: https://github.com/homebysix/pre-commit-macadmin/compare/v1.8.0...v1.8.1
[1.8.0]: https://github.com/homebysix/pre-commit-macadmin/compare/v1.7.0...v1.8.0
[1.7.0]: https://github.com/homebysix/pre-commit-macadmin/compare/v1.6.2...v1.7.0
[1.6.2]: https://github.com/homebysix/pre-commit-macadmin/compare/v1.6.1...v1.6.2
[1.6.1]: https://github.com/homebysix/pre-commit-macadmin/compare/v1.6.0...v1.6.1
[1.6.0]: https://github.com/homebysix/pre-commit-macadmin/compare/v1.5.2...v1.6.0
[1.5.2]: https://github.com/homebysix/pre-commit-macadmin/compare/v1.5.1...v1.5.2
[1.5.1]: https://github.com/homebysix/pre-commit-macadmin/compare/v1.5.0...v1.5.1
[1.5.0]: https://github.com/homebysix/pre-commit-macadmin/compare/v1.4.0...v1.5.0
[1.4.0]: https://github.com/homebysix/pre-commit-macadmin/compare/v1.3.0...v1.4.0
[1.3.0]: https://github.com/homebysix/pre-commit-macadmin/compare/v1.2.1...v1.3.0
[1.2.1]: https://github.com/homebysix/pre-commit-macadmin/compare/v1.2.0...v1.2.1
[1.2.0]: https://github.com/homebysix/pre-commit-macadmin/compare/v1.1.4...v1.2.0
[1.1.4]: https://github.com/homebysix/pre-commit-macadmin/compare/v1.1.3...v1.1.4
[1.1.3]: https://github.com/homebysix/pre-commit-macadmin/compare/v1.1.2...v1.1.3
[1.1.2]: https://github.com/homebysix/pre-commit-macadmin/compare/v1.1.1...v1.1.2
[1.1.1]: https://github.com/homebysix/pre-commit-macadmin/compare/v1.1.0...v1.1.1
[1.1.0]: https://github.com/homebysix/pre-commit-macadmin/compare/v1.0.5...v1.1.0
[1.0.5]: https://github.com/homebysix/pre-commit-macadmin/compare/v1.0.4...v1.0.5
[1.0.4]: https://github.com/homebysix/pre-commit-macadmin/compare/v1.0.3...v1.0.4
[1.0.3]: https://github.com/homebysix/pre-commit-macadmin/compare/v1.0.2...v1.0.3
[1.0.2]: https://github.com/homebysix/pre-commit-macadmin/compare/v1.0.1...v1.0.2
[1.0.1]: https://github.com/homebysix/pre-commit-macadmin/compare/v1.0.0...v1.0.1
