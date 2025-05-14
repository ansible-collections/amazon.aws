# CI

## AWS Collections

GitHub Actions are used to run the Continuous Integration for amazon.aws collection. The workflows used for the CI can be found [here](https://github.com/ansible-collections/amazon.aws/tree/stable-10/.github/workflows). These workflows include jobs to run the unit tests, integration tests, sanity tests, linters, changelog check and doc related checks. The following table lists the python and ansible versions against which these jobs are run.

| Jobs | Description | Python Versions | Ansible Versions |
| ------ |-------| ------ | -----------|
| changelog |Checks for the presence of Changelog fragments | 3.9 | devel |
| Linters | Runs `black` and `flake8` on plugins and tests | 3.9 | devel |
| Sanity | Runs ansible sanity checks | 3.11, 3.12, 3.13 | devel, milestone, stable-2.17 (Also 3.10, Not 3.13), stable-2.18, stable-2.19 |
| Unit tests | Executes the unit test cases | 3.11, 3.12, 3.13 | devel, milestone, stable-2.17 (Also 3.10, Not 3.13), stable-2.18, stable-2.19 |
| Integration tests | Executes the integration test suites| <TBA> | <TBA> |
