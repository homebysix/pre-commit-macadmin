# Pre-Commit Hooks for Mac Admins

This repository contains hooks for [pre-commit](https://pre-commit.com/hooks.html) that may be useful to Mac admins, client engineers, and other Apple-focused IT professionals.

## Requirements

To use these hooks, you first need to install pre-commit using the instructions here:
https://pre-commit.com/#install

## Adding hooks to your pre-commit config

For any hook in this repo you wish to use, add the following to your pre-commit config:

```
-   repo: https://github.com/homebysix/pre-commit-macadmin
    rev: v1.0.0
    hooks:
    -   id: check-plists
    # -   id: ...
```

## Hooks available

### AutoPkg

- __check-autopkg-recipe-list__
    This hook checks AutoPkg recipe lists (in txt, plist, yaml, or json format) for common issues.

- __check-autopkg-recipes__
    This hook checks AutoPkg recipes to ensure they contain required top-level keys. (https://github.com/autopkg/autopkg/wiki/Recipe-Format)
    - Specify your preferred AutoPkg recipe override prefix, if you wish to enforce it:  
        `[--override-prefix]` (default: `local.`)

- __forbid-autopkg-overrides__
    This hook prevents AutoPkg overrides from being added to the repo.

### Jamf

- __check-jamf-extension-attributes__
    This hook checks Jamf extension attributes for common issues. (Looks for EAs in a path containing jamf/extension_attributes or jss/extension_attributes.)

- __check-jamf-scripts__
    This hook checks Jamf scripts for common issues. (Looks for scripts in a path containing jamf/scripts or jss/scripts.)

- __check-jamf-profiles__
    This hook checks Jamf profiles for common issues. (Looks for profiles in a path containing jamf/profiles or jss/profiles.)

### Munki

- __check-munki-pkgsinfo__
    This hook checks Munki pkginfo files to ensure they are valid.
    - Specify your preferred list of pkginfo categories, if you wish to enforce it:  
        `['--categories=Productivity,Design,Utilities']`
    - Specify required pkginfo keys:  
        `['--required-keys=category,description,developer,name,version']` (default: category, description, developer, name)

- __check-munkiadmin-scripts__
    This hook ensures MunkiAdmin scripts are executable.

- __check-munkipkg-buildinfo__
    This hook checks MunkiPkg build-info files to ensure they are valid.

- __munki-makecatalogs__
    This hook runs the "makecatalogs" command to ensure all referenced packages are present and catalogs are up to date.

### Outset

- __check-outset-scripts__
    This hook checks Outset scripts to ensure they're executable.

### General

- __check-plists__
    This hook checks XML property list (plist) files for basic syntax errors.

## Recommendations

If you find my hooks useful, you may also want to use one or more of the Python, Markdown, and Git-related hooks listed here:
https://pre-commit.com/hooks.html

Specifically, here are a few I use for Mac admin work:
- `check-added-large-files`
- `check-executables-have-shebangs`
- `check-merge-conflict`
- `check-yaml`
- `detect-aws-credentials`
- `detect-private-key`
- `mixed-line-ending`
- `no-commit-to-branch`
- `trailing-whitespace`
