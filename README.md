# Pre-Commit Hooks for Mac Admins

![CodeQL](https://github.com/homebysix/pre-commit-macadmin/workflows/CodeQL/badge.svg)

This repository contains hooks for [pre-commit](https://pre-commit.com/hooks.html) that may be useful to Mac admins, client engineers, and other Apple-focused IT professionals.

## Requirements

To use these hooks, you first need to install pre-commit using the instructions here:
https://pre-commit.com/#install

## Adding hooks to your pre-commit config

For any hook in this repo you wish to use, add the following to your pre-commit config:

```yaml
-   repo: https://github.com/homebysix/pre-commit-macadmin
    rev: v1.9.0
    hooks:
    -   id: check-plists
    # -   id: ...
```

After adding a hook to your pre-commit config, it's not a bad idea to run `pre-commit autoupdate` to ensure you have the latest version of the hooks.

## Hooks available

### General

- __check-git-config-email__

    This hook checks to ensure the Git config email matches one of the specified domains:
        `args: ['--domains', 'pretendco.com', 'contoso.com', '--']`

- __check-plists__

    This hook checks XML property list (plist) files for basic syntax errors.

- __check-munkipkg-buildinfo__

    This hook checks [MunkiPkg](https://github.com/munki/munki-pkg) build-info files to ensure they are valid.

- __check-outset-scripts__

    This hook checks [Outset](https://github.com/chilcote/outset) scripts to ensure they're executable.

### [AutoPkg](https://github.com/autopkg/autopkg)

- __check-autopkg-recipe-list__

    This hook checks AutoPkg recipe lists (in txt, plist, yaml, or json format) for common issues.

- __check-autopkg-recipes__

    This hook checks AutoPkg recipes to ensure they meet various requirements.

    - Optionally specify your preferred AutoPkg recipe and/or override prefix, if you wish to enforce them:
        `args: ['--override-prefix=com.yourcompany.autopkg.']`  
        (default: `local.`)  
        `args: ['--recipe-prefix=com.github.yourusername.']`  
        (default: `com.github.`)

    - Optionally specify the version of AutoPkg for which you want to ignore MinimumVersion mismatches with processors.
        `args: ['--ignore-min-vers-before=0.5.0']`  
        (default: `1.0.0`)  
        Specifying `0.1.0` will not ignore any MinimumVersion mismatches.

    - If you're a purist, you can also enable strict mode. This enforces recipe type conventions, all processor/MinimumVersion mismatches, and forbids `<!-- -->` style comments.  
        `args: ['--strict']`  
        (default: False)

- __forbid-autopkg-overrides__

    This hook prevents AutoPkg overrides from being added to the repo.

- __forbid-autopkg-trust-info__

    This hook prevents AutoPkg recipes with trust info from being added to the repo.

### [Jamf](https://www.jamf.com/)

- __check-jamf-extension-attributes__

    This hook checks Jamf extension attributes for common issues. (Looks for EAs in a path containing jamf/extension_attributes or jss/extension_attributes.)

- __check-jamf-scripts__

    This hook checks Jamf scripts for common issues. (Looks for scripts in a path containing jamf/scripts or jss/scripts.)

- __check-jamf-profiles__

    This hook checks Jamf profiles for common issues. (Looks for profiles in a path containing jamf/profiles or jss/profiles.)

### [Munki](https://github.com/munki/munki)

- __check-munki-pkgsinfo__

    This hook checks Munki pkginfo files to ensure they are valid.

    - Specify your preferred list of pkginfo catalogs, if you wish to enforce it, followed by `--` to signal the end of the list:  
        `args: ['--catalogs', 'testing', 'stable', '--']`

    - Specify your preferred list of pkginfo categories, if you wish to enforce it, followed by `--`:  
        `args: ['--categories', 'Productivity', 'Design', 'Utilities', 'Web Browsers', '--']`

    - Specify required pkginfo keys, followed by `--`:  
        `args: ['--required-keys', 'category', 'description', 'developer', 'name', 'version', '--']`  
        (default: description, name)

- __check-munkiadmin-scripts__

    This hook ensures MunkiAdmin scripts are executable.

- __munki-makecatalogs__

    This hook runs the "makecatalogs" command to ensure all referenced packages are present and catalogs are up to date.

## Note about combining arguments

When combining arguments that take lists (for example: `--required-keys`, `--catalogs`, and `--categories`), only the _last_ list needs to have a trailing `--`. For example, if you use the check-munki-pkgsinfo hook with only the `--catalogs` argument, your yaml config would look like this:

```yaml
-   repo: https://github.com/homebysix/pre-commit-macadmin
    rev: v1.9.0
    hooks:
    -   id: check-munki-pkgsinfo
        args: ['--catalogs', 'testing', 'stable', '--']
```

But if you also use the `--categories` argument, you would move the trailing `--` to the end, after all the lists, like this:

```yaml
-   repo: https://github.com/homebysix/pre-commit-macadmin
    rev: v1.9.0
    hooks:
    -   id: check-munki-pkgsinfo
        args: ['--catalogs', 'testing', 'stable', '--categories', 'Design', 'Engineering', 'Web Browsers', '--']
```

The `--` only serves as a signal to the hook that the list of arguments is complete, and is only needed for "list" type arguments.

If it looks better to your eye, feel free to use a multi-line list for long arguments:

```yaml
-   repo: https://github.com/homebysix/pre-commit-macadmin
    rev: v1.9.0
    hooks:
    -   id: check-munki-pkgsinfo
        args: [
            '--required-keys', 'description', 'name', 'developer', 'category', 'version',
            '--catalogs', 'testing', 'stable',
            '--categories', 'Communication', 'Design', 'Engineering', 'macOS', 'Printers',
                'Productivity', 'Security',  'Utilities', 'Web Browsers',
            '--']
```

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
