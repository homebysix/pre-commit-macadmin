# Releasing new versions of pre-commit-macadmin

Releases are largely automated via GitHub Actions. The workflow triggers when `setup.py` is pushed to `main`, creating a GitHub release and automatically preparing the `dev` branch for the next release.

## Release Process

1. Determine the version to release. After each release, the workflow auto-bumps `setup.py` on `dev` to the next **patch** version — so for a normal patch release, `setup.py` on `dev` already holds the correct next version; use that value as-is in the steps below. Only edit `setup.py` yourself first if you're bumping the **minor** or **major** version instead (see [Version Numbering](#version-numbering)).

1. On the `dev` branch, check unit tests:

        .venv/bin/python -m coverage run -m unittest discover -vs tests

1. Update the generated AutoPkg processor version table from a local AutoPkg checkout:

        .venv/bin/python scripts/generate_autopkg_processor_versions.py --autopkg-repo ../autopkg
        .venv/bin/python -m coverage run -m unittest discover -vs tests

   Use `--full` when the generator logic changes, historical AutoPkg tags are added or corrected, or you need to rebuild from AutoPkg `0.1.0`. The default mode appends stable releases newer than the checked-in `last_walked_version`.

1. Prepare CHANGELOG.md for release by moving `[Unreleased]` changes to a new version section, using the version determined in step 1 above for `X.Y.Z`:

        ## [Unreleased]

        Nothing yet.

        ## [X.Y.Z] - YYYY-MM-DD

        ### Added/Changed/Fixed/Removed (separate sections as applicable)
        - New features, changes, fixes, or removals

   The release workflow will extract this section for the GitHub release notes.

1. Add the version comparison link at the bottom of CHANGELOG.md:

        [X.Y.Z]: https://github.com/homebysix/pre-commit-macadmin/compare/vPREVIOUS...vX.Y.Z

1. Confirm the version in `setup.py` matches the CHANGELOG version (e.g., `2.3.6`). For a normal patch release this should already be true from the auto-bump; only change it here if you're doing a minor/major release.

1. Update the version in `README.md` examples to match (e.g., `rev: v2.3.6`).

1. Commit these changes to `dev` and push.

1. Merge `dev` branch to `main`.

1. The release workflow will automatically:
   - Detect the version from `setup.py` (e.g., `2.3.6`)
   - Create a GitHub release with tag `v2.3.6`
   - Extract release notes from CHANGELOG.md
   - Merge `main` back to `dev`
   - Bump `dev` versions to the next patch version (e.g., `2.3.7`) in `setup.py` and `README.md`
   - Commit and push the updated version to `dev`

   Note: CHANGELOG.md is NOT automatically updated on `dev`. Add entries to the `[Unreleased]` section as you make changes.

1. Pull the updated `dev` branch to continue development at the new version.

1. As you make changes, add entries to the `[Unreleased]` section of CHANGELOG.md. When ready for the next release, simply promote those changes to a new version section (repeat from step 2) - no need to manually bump versions unless you want to change to a minor or major version.

1. After each release, verify on GitHub and run `pre-commit autoupdate` on a test repo to confirm it updates correctly.

## Version Numbering

The workflow automatically bumps the **patch** version (X.Y.Z → X.Y.Z+1). If you need to bump the **minor** or **major** version, manually update the version numbers in `setup.py`, `README.md`, and CHANGELOG.md before merging to `main`.

## Pre-releases

If a pre-release is desired for testing purposes, it must be done manually.
