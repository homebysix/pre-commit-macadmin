# Releasing new versions of pre-commit-macadmin

1. Update the versions in __README.md__ and __setup.py__.

1. Check unit tests:

        venv/bin/python -m coverage run -m unittest discover -vs tests

1. Update the change log.

1. Merge development branch to main.

1. Create a GitHub release with version tag, prefixed with `v`. (For example: `v2.3.4`)

1. Run `pre-commit autoupdate` on a test repo and confirm it updates to the new version.
