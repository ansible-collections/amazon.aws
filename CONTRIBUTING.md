# Contributing

## AWS Collections

There are two related collections containing AWS content (modules and plugins).

### amazon.aws
This collection contains the `module_utils` (shared libraries) used by both collections.
Content in this collection is included downstream in Red Hat Ansible Automation Platform.

Code standards, test coverage, and other supportability criteria may be higher in this collection.

The `amazon.aws` collection is an [Ansible-maintained collection](https://docs.ansible.com/ansible/devel/community/contributing_maintained_collections.html).

### community.aws
This collection contains modules and plugins contributed and maintained by the Ansible AWS
community.  The `community.aws` collection is tested and generally assured to work in
conjunction with `amazon.aws`.

New modules and plugins developed by the community should be proposed to `community.aws`.
Content in this collection that is stable and meets other acceptance criteria has the potential
to be promoted and migrated into `amazon.aws`.

## Submitting Issues
All software has bugs, and the `amazon.aws` collection is no exception. When you find a bug,
you can help tremendously by [telling us about it](https://github.com/ansible-collections/amazon.aws/issues/new/choose).

If you should discover that the bug you're trying to file already exists in an issue,
you can help by verifying the behavior of the reported bug with a comment in that
issue, or by reporting any additional information

## Development Setup

### Environment setup

This collection uses [uv](https://docs.astral.sh/uv/) to manage the developer
toolchain. The toolchain is pinned in `uv.lock`, which is committed, so every
contributor and CI resolve exactly the same versions.

First, [install uv](https://docs.astral.sh/uv/getting-started/installation/)
(once per machine):

```
# macOS / Linux
curl -LsSf https://astral.sh/uv/install.sh | sh

# or, with Homebrew
brew install uv
```

Then, from a clean checkout:

```
uv sync --dev                                  # create .venv from uv.lock
uv run prek install                            # enable the git pre-commit hooks
uv pip install -r requirements.txt             # AWS SDK runtime dependencies
uv tool install ansible-dev-environment        # once per machine
ade install --editable --no-seed .             # editable collection install
```

`ade install --editable` puts this checkout on the Ansible collection path as
`ansible_collections/amazon/aws`, which is required for the collection's imports
to resolve. It generates a local `.ansible.cfg` and a `.venv`; both are
git-ignored and excluded from the built Galaxy artifact.

> **Note:** runtime dependencies will move to `meta/ee-requirements.txt` as part
> of the dependency consolidation work. Until then, install them from
> `requirements.txt` as shown above.

### Pre-commit Hooks

This collection uses [prek](https://github.com/j178/prek) to manage Git pre-commit
hooks, catching formatting and lint problems at commit time rather than in CI.
prek is a drop-in replacement for `pre-commit` and consumes the same
`.pre-commit-config.yaml`. CI enforces `ansible-lint` as a required status check, so
running the hooks locally keeps your commits green before you push.

`prek` is part of the `dev` dependency group, so `uv sync --dev` (above) already
installs it into `.venv`; there is no separate install step. `uv run prek install`
sets up the Git hook so the configured hooks run automatically on each `git commit`.
To run all hooks manually against every file:

```
uv run prek run --all-files
```

The current hook set applies basic hygiene checks (trailing whitespace, end-of-file
newlines, large-file guard, line endings, and blocking direct commits to `main`),
runs `ruff-check` and `ruff-format` (pinned to the same Ruff version as
`pyproject.toml` / tox), and runs `ansible-lint` (which invokes yamllint
internally; there is no separate `.yamllint` file).

To run the same Python lint/format checks outside prek:

```
tox -e ruff-lint   # check only (no rewrite)
tox -e ruff        # apply ruff check --fix and ruff format
```

### Running tests and linters

`tox` and the `tox-uv-bare` plugin are part of the dev group, so tox provisions
its environments through uv with no separate pip bootstrap:

```
uv run tox -m lint                             # linters (black, isort, flynt, flake8)
uv run tox -m unit                             # the full unit test matrix
uv run tox -e ansible2.20-py314-with_constraints   # a single unit environment
uv run tox -l                                  # list every environment
```

Test dependencies are deliberately not in `pyproject.toml`; they live in
`tests/unit/requirements.txt` and `tests/integration/requirements.txt` so that
`ansible-test` keeps working without uv.

## Writing New Code

New modules should be submitted to the [community.aws](https://github.com/ansible-collections/community.aws) collection.

For new features and bug fixes on existing modules,
clone this repository and try to run unit tests and integration tests by following
[these instructions](https://docs.ansible.com/ansible/latest/community/create_pr_quick_start.html).
When you get to this part:

```
ansible-test integration name_of_test_subdirectory --docker -v
```

Run this from the `tests` directory of this repository.
Substitute `name_of_test_subdirectory` for the name of the relevant directory within `tests/integration/targets`.
You'll get this error:

```
WARNING: Excluding tests marked "cloud/aws" which require config
(see "/home/dev/ansible/ansible/test/lib/ansible_test/config/cloud-config-aws.ini.template"): ec2_group
```
This is because the unit tests don't automatically detect the AWS credentials on your machine
unlike plain `boto3` and the `aws` cli.
(Typically because they're run inside Docker, which can't access `~/.aws/credentials`.
But even when running tests outside docker, the tests ignore `~/.aws/credentials`.)
You need to explicitly create credentials and load them in to an Ansible-specific file.
To do this, copy the file mentioned in that error message,
into the clone of this repo, under `tests/integration/cloud-config-aws.ini`.
Modify the `@` variables, pasting in an IAM secret credential.
If you don't need the `secret_token` (most IAM users don't), comment that line out.

You can use an AWS account that already has unrelated resources in it.
The tests should not touch pre-existing resources, and should tidy up after themselves.
(Of course for security reasons you may want to run in a dedicated AWS account.)

If you're only writing a pull request for one AWS service
you are able to create credentials only with permissions required for that test.
For example, to test the Lambda modules, you only need Lambda permissions,
and permissions to create IAM roles.
You could also deploy [the policies used by the CI](https://github.com/mattclay/aws-terminator/tree/master/aws/policy).

All modules MUST have integration tests for new features.
Bug fixes for modules that currently have integration tests SHOULD have tests added.

Once you're able to run integration tests for the existing code,
now start by adding tests in `tests/integration/targets`
for your new feature or tests for the bug(s) you're about to fix.

Expected test criteria:
* Resource creation under check mode
* Resource creation
* Resource creation again (idempotency) under check mode
* Resource creation again (idempotency)
* Resource modification under check mode
* Resource modification
* Resource modification again (idempotency) under check mode
* Resource modification again (idempotency)
* Resource deletion under check mode
* Resource deletion
* Resource deletion (of a non-existent resource) under check mode
* Resource deletion (of a non-existent resource)

Where modules have multiple parameters we recommend running through the 4-step modification cycle for each parameter the module accepts, as well as a modification cycle where as most, if not all, parameters are modified at the same time.

After writing the tests, now write/modify the module code, typically in `plugins/modules`.
Don't forget to add [a changelog entry](https://docs.ansible.com/ansible/latest/community/collection_development_process.html#collection-changelog-fragments).
Then create a pull request.

If you're struggling with running integration tests locally, don't worry.
After creating a pull request the GitHub Actions will automatically test for you.

## Running Tests Locally

### Unit Tests

Unit tests are run via [tox](https://tox.wiki/). The collection uses fully-qualified
`ansible_collections.amazon.aws.*` imports, which require the Ansible collection loader
to resolve the namespace correctly. `tox` handles this automatically by syncing the
collection into a managed environment before running `pytest`.

First, install `tox` into your virtual environment:

```bash
pip install tox
```

To see the available tox environments:

```bash
tox list
```

To run unit tests in a specific environment matching your Python and
ansible-core versions:

```bash
tox -e ansible2.20-py312-without_constraints
```

To run the full unit-test matrix, use the `unit` tox label:

```bash
tox -m unit
```

For a faster check of the supported range, use `tox -m unit-oldest` or
`tox -m unit-newest`.

To run a specific test file or filter by test name, use the `-k` flag rather than
passing a file path directly (file paths resolve relative to the repo root and break
the collection namespace resolution inside tox):

```bash
tox -e ansible2.20-py312-without_constraints -- -k test_aws_sqs_queue -v
```

See `tox.ini` for details about the available ansible-core and Python version
combinations.

> **Note:** Running `pytest` directly does not set up the collection namespace and can
> fail with `ModuleNotFoundError: No module named 'ansible_collections'`. Use tox for
> local unit tests, or use `ansible-test units --docker` as described in the Ansible
> developer documentation.

### Linting

The CI lint job runs every tox environment labeled `lint`. Run the complete lint suite
against the collection with:

```bash
tox -m lint
```

To automatically fix formatting issues, run the format environments:

```bash
tox -m format
```

To check coverage for new or changed code, run the unit tests first and then:

```bash
tox -e diff-cover
```

## More information about contributing

General information about setting up your Python environment, testing modules,
Ansible coding styles, and more can be found in the [Ansible Community Guide](
https://docs.ansible.com/ansible/latest/community/index.html).

Information about AWS SDK library usage, module utils, testing, and more can be
found in the [AWS Guidelines](https://docs.ansible.com/ansible/devel/collections/amazon/aws/docsite/dev_guidelines.html#ansible-collections-amazon-aws-docsite-dev-guide-intro)
documentation.

For general information on running the integration tests see
[this page](https://docs.ansible.com/ansible/latest/community/collection_contributors/test_index.html) and
[Integration Tests page of the Module Development Guide](https://docs.ansible.com/ansible/devel/dev_guide/testing_integration.html#non-destructive-tests).
Ignore the part about `source hacking/env-setup`. That's only applicable for working on `ansible-core`.
You should be able to use the `ansible-test` that's installed with Ansible generally.
Look at [the section on configuration for cloud tests](https://docs.ansible.com/ansible/devel/dev_guide/testing_integration.html#other-configuration-for-cloud-tests).

- [Ansible Community Guide](https://docs.ansible.com/ansible/latest/community/index.html) - Details on contributing to Ansible
- [Contributing to Collections](https://docs.ansible.com/ansible/devel/dev_guide/developing_collections.html#contributing-to-collections) - How to check out collection git repositories correctly
- [Contributing to Ansible-maintained collections](https://docs.ansible.com/ansible/devel/community/contributing_maintained_collections.html#contributing-maintained-collections)
- [Guidelines for Ansible Amazon AWS module development](https://docs.ansible.com/ansible/latest/collections/amazon/aws/docsite/dev_guidelines.html)
- [Getting Started With AWS Ansible Module Development and Community Contribution](https://www.ansible.com/blog/getting-started-with-aws-ansible-module-development)

### Code of Conduct
The `amazon.aws` collection follows the Ansible project's
[Code of Conduct](https://docs.ansible.com/ansible/devel/community/code_of_conduct.html).
Please read and familiarize yourself with this document.
