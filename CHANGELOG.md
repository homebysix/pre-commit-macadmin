# pre-commit-macadmin change log

All notable changes to this project will be documented in this file. This project adheres to [Semantic Versioning](http://semver.org/).

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


[Unreleased]: https://github.com/homebysix/pre-commit-macadmin/compare/v1.8.2...HEAD
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
