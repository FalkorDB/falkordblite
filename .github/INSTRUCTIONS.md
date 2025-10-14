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
- **Publishes**: Uploads the packages to PyPI (requires `PYPI_API_TOKEN` secret)

## Secrets Required

To use the publish workflow, you need to configure the following secret in your repository settings:

- `PYPI_API_TOKEN`: Your PyPI API token for authentication

## Manual Triggering

Both workflows support manual triggering via the GitHub Actions UI using the `workflow_dispatch` event.
