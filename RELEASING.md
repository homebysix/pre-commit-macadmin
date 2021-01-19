# Releasing new versions of pre-commit-macadmin

1. Update the versions in __README.md__ and __pre_commit_hooks/\_\_init\_\_.py__.

1. Update the change log.

1. Merge development branch to main.

1. Create a GitHub release with version tag, prefixed with `v`. (For example: `v2.3.4`)

1. Run `pre-commit autoupdate` on a test repo and confirm it updates to the new version.
