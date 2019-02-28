#!/usr/bin/python

from setuptools import setup

setup(
    name="pre-commit-macadmin",
    description="Pre-commit hooks for Mac admins, client engineers, and IT consultants.",
    # url="https://github.com/homebysix/pre-commit-macadmin",
    version="1.0.0",
    author="Elliot Jordan",
    author_email="elliot@elliotjordan.com",
    packages=["pre_commit_hooks"],
    entry_points={
        "console_scripts": (
            "check-plists = pre_commit_hooks.check_plists:main",
        )
    },
)
