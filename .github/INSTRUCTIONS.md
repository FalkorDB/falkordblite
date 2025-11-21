# GitHub Actions Workflows

This directory contains the CI/CD workflows for FalkorDBLite.

## Workflows

### CI Workflow (`ci.yml`)

Runs on every push and pull request to `master`/`main` branches. This workflow:

- **Tests**: Runs the test suite across Python versions 3.8, 3.9, 3.10, 3.11, and 3.12
- **Verification**: Executes the `verify_install.py` script to ensure installation works correctly
- **Linting**: Runs code quality checks with `pylint` and `pycodestyle`
- **Build**: Builds source distribution and wheel packages
- **Coverage**: Uploads code coverage results to Codecov

### Publish Workflow (`publish.yml`)

Triggered when a new release is published. This workflow:

- **Builds**: Creates source distribution and wheel packages
- **Validates**: Checks package integrity with `twine check`
- **Publishes**: Uploads the packages to PyPI using Trusted Publishing (OIDC)

## PyPI Configuration Required

This workflow uses PyPI's Trusted Publishing feature, which eliminates the need for API tokens. To set this up:

1. Log in to PyPI as the package owner
2. Navigate to your package's settings
3. Add a new "Trusted Publisher" with the following details:
   - **Owner**: FalkorDB
   - **Repository name**: falkordblite
   - **Workflow name**: publish.yml
   - **Environment name**: (leave empty)

For more information, see: https://docs.pypi.org/trusted-publishers/

## Manual Triggering

Both workflows support manual triggering via the GitHub Actions UI using the `workflow_dispatch` event.
