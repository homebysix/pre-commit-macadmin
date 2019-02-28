#!/usr/bin/python

from setuptools import setup

setup(
    name="pre-commit-macadmin",
    description="Pre-commit hooks for Mac admins, client engineers, and IT consultants.",
    url="https://github.com/homebysix/pre-commit-macadmin",
    version="1.0.0",
    author="Elliot Jordan",
    author_email="elliot@elliotjordan.com",
    packages=["pre_commit_hooks"],
    entry_points={
        "console_scripts": [
            "check-autopkg-recipe-list = pre_commit_hooks.check_autopkg_recipe_list:main",
            "check-autopkg-recipes = pre_commit_hooks.check_autopkg_recipes:main",
            "check-munki-pkgsinfo = pre_commit_hooks.check_munki_pkgsinfo:main",
            "check-munkiadmin-scripts = pre_commit_hooks.check_munkiadmin_scripts:main",
            "check-munkipkg-buildinfo = pre_commit_hooks.check_munkipkg_buildinfo:main",
            "check-plists = pre_commit_hooks.check_plists:main",
            "forbid-autopkg-overrides = pre_commit_hooks.forbid_autopkg_overrides:main",
            "munki-makecatalogs = pre_commit_hooks.munki_makecatalogs:main",
        ]
    },
)
