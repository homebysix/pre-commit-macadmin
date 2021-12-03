#!/usr/bin/python
# -*- coding: utf-8 -*-

from setuptools import setup

setup(
    name="pre-commit-macadmin",
    description="Pre-commit hooks for Mac admins, client engineers, and IT consultants.",
    url="https://github.com/homebysix/pre-commit-macadmin",
    version="1.12.0",
    author="Elliot Jordan",
    author_email="elliot@elliotjordan.com",
    packages=["pre_commit_hooks"],
    install_requires=["ruamel.yaml>=0.15"],
    entry_points={
        "console_scripts": [
            "check-autopkg-recipe-list = pre_commit_hooks.check_autopkg_recipe_list:main",
            "check-autopkg-recipes = pre_commit_hooks.check_autopkg_recipes:main",
            "check-git-config-email = pre_commit_hooks.check_git_config_email:main",
            "check-jamf-extension-attributes = pre_commit_hooks.check_jamf_extension_attributes:main",
            "check-jamf-json-schemas = pre_commit_hooks.check_jamf_json_schemas:main",
            "check-jamf-profiles = pre_commit_hooks.check_jamf_profiles:main",
            "check-jamf-scripts = pre_commit_hooks.check_jamf_scripts:main",
            "check-munki-pkgsinfo = pre_commit_hooks.check_munki_pkgsinfo:main",
            "check-munkiadmin-scripts = pre_commit_hooks.check_munkiadmin_scripts:main",
            "check-munkipkg-buildinfo = pre_commit_hooks.check_munkipkg_buildinfo:main",
            "check-outset-scripts = pre_commit_hooks.check_outset_scripts:main",
            "check-plists = pre_commit_hooks.check_plists:main",
            "check-preference-manifests = pre_commit_hooks.check_preference_manifests:main",
            "forbid-autopkg-overrides = pre_commit_hooks.forbid_autopkg_overrides:main",
            "forbid-autopkg-trust-info = pre_commit_hooks.forbid_autopkg_trust_info:main",
            "munki-makecatalogs = pre_commit_hooks.munki_makecatalogs:main",
        ]
    },
)
