# Continuous Integration (CI)

## AWS Upstream Testing

GitHub Actions are used to run the CI for the amazon.aws collection. The workflows used for the CI can be found [here](https://github.com/ansible-collections/amazon.aws/tree/main/.github/workflows). These workflows include jobs to run the unit tests, sanity tests, linters, and changelog checks.

The collection uses reusable workflows from [ansible-network/github_actions](https://github.com/ansible-network/github_actions) for standardized testing.

To learn more about the testing strategy, see [this proposal](https://github.com/ansible-collections/cloud-content-handbook/blob/main/Proposals/core_collection_dependency.md).

### PR Testing Workflows

The following tests run on every pull request:

| Job | Description | Python Versions | ansible-core Versions |
| --- | ----------- | --------------- | --------------------- |
| Changelog | Checks for the presence of changelog fragments | 3.12 | devel |
| Linters | Runs `black` and `flake8` on plugins and tests | 3.10 | devel |
| Sanity | Runs ansible sanity checks | See compatibility table below | devel, stable-2.17, stable-2.18, stable-2.19, stable-2.20 |
| Unit tests | Executes unit test cases | See compatibility table below | devel, stable-2.17, stable-2.18, stable-2.19, stable-2.20 |
| Integration tests | Executes integration test suites (handled by Zuul) | >=3.8 | Zuul build pipeline |

### Python Version Compatibility by ansible-core Version

These are outlined in the collection's [/tox.ini](/tox.ini) file (`envlist`) and GitHub Actions workflow exclusions.

| ansible-core Version | Sanity Tests | Unit Tests |
| -------------------- | ------------ | ---------- |
| devel | 3.12, 3.13, 3.14 | 3.12, 3.13 |
| stable-2.20 | 3.12, 3.13, 3.14 | 3.12, 3.13 |
| stable-2.19 | 3.11, 3.12, 3.13 | 3.11, 3.12, 3.13 |
| stable-2.18 | 3.11, 3.12, 3.13 | 3.11, 3.12, 3.13 |
| stable-2.17 | 3.10, 3.11, 3.12 | 3.10, 3.11, 3.12 |
