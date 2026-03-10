# SonarQube Cloud in amazon.aws

SonarQube Cloud (SonarCloud) is a Software-as-a-Service (SaaS) code analysis tool that helps maintain code quality by identifying issues related to maintainability, reliability, and security.

The amazon.aws collection uses SonarQube Cloud to analyze the `main` branch and pull requests, and to track unit test coverage and quality gate compliance.

## Core concepts

1. **Clean as You Code**: Development practice where new code must meet quality standards.

2. **Clean Code Attributes**: Consistency, Intentionality, Adaptability, and Responsibility. See [Code analysis metrics](https://docs.sonarsource.com/sonarqube-cloud/digging-deeper/metric-definitions/).

3. **Software Quality**: SonarQube Cloud evaluates quality by flagging issues that violate clean code principles.

4. **Quality Standards**: Defined by a quality profile (rules) and a quality gate (conditions that must pass). The gate shows pass or fail based on whether all conditions are met.

## Analysis method: CI-based analysis

The collection uses **CI-based analysis** with GitHub Actions:

- The SonarScanner runs inside the CI build.
- Configuration is controlled in the repository (properties file and workflow).
- **Code coverage** is produced by a dedicated coverage job (via `tox`) before the SonarCloud workflow runs; coverage reports are downloaded and passed to the scanner.

Automatic analysis is not used because it does not support code coverage and has limited branch support.

References:

- [CI-Based Analysis overview](https://docs.sonarsource.com/sonarqube-cloud/advanced-setup/ci-based-analysis/overview-of-integrated-cis/)
- [Test coverage in SonarCloud](https://docs.sonarsource.com/sonarqube-cloud/enriching/test-coverage/overview/)

## Configuration files

### `sonar-project.properties`

Project-level analysis settings live in `sonar-project.properties` at the repository root:

| Parameter | Value | Purpose |
|-----------|--------|---------|
| `sonar.projectKey` | `ansible-collections_amazon.aws` | SonarCloud project identifier |
| `sonar.organization` | `ansible-collections` | SonarCloud organization |
| `sonar.projectName` | `amazon.aws` | Display name |
| `sonar.sources` | `.` | Root of analyzed source tree |
| `sonar.tests` | `tests/unit,tests/integration` | Test directories (for test-aware analysis) |
| `sonar.exclusions` | `tests/**,.tox/**` | Paths excluded from analysis |
| `sonar.python.coverage.reportPaths` | `coverage.xml` | Default coverage report path (overridden by CI when present) |
| `sonar.python.version` | `3.13` | Python version for analysis |
| `sonar.newCode.referenceBranch` | `main` | Branch used as baseline for "new code" |

Full reference: [Analysis parameters](https://docs.sonarqube.org/latest/analysis/analysis-parameters/).

### `tox.ini` (coverage generation)

Unit test coverage is produced by **tox**. The default test environment runs `pytest` with `pytest-cov`:

- **Coverage scope**: `plugins/callback`, `plugins/inventory`, `plugins/lookup`, `plugins/module_utils`, `plugins/modules`, `plugins/plugin_utils`, and `plugins`.
- **Reports**: HTML (`--cov-report html`) and Cobertura XML (`--cov-report xml:coverage.xml`).
- **Output**: `coverage.xml` is written under the `tox` environment directory (e.g. `.tox/ansible2.20-py314-with_constraints/...`).

The CI coverage job uses the environment `ansible2.20-py314-with_constraints` so that a single, consistent coverage report is produced for SonarCloud.

### `pyproject.toml` (coverage and `pytest`)

`pyproject.toml` does not define SonarQube-specific settings. It configures tools used by tests and coverage:

- **`[tool.pytest]`**: Pytest options (e.g. `xfail_strict = true`).
- **`[tool.coverage.report]`**: Coverage report options, including `also_exclude` for lines that are not required to be covered (e.g. `raise NotImplementedError`).

These affect how coverage is generated (and thus what appears in `coverage.xml`), but SonarCloud is configured only via `sonar-project.properties` and the workflow arguments.

## GitHub Actions integration

Two workflows implement the integration:

1. **`all_green`** (`.github/workflows/all_green_check.yml`) runs on pull requests and pushes to `main` and `stable-*`. It runs linters, sanity, units, and a **coverage** job. When all required jobs succeed, it triggers the SonarCloud workflow via `workflow_run`.

2. **SonarCloud** (`.github/workflows/sonarcloud.yml`) runs after **all_green** completes successfully. It checks out the repo, downloads the coverage artifact from that run, locates the coverage XML, gathers PR metadata when applicable, and runs the SonarScanner with the appropriate arguments (including coverage paths).

### Why `workflow_run`

- **Secrets**: Workflows triggered by `pull_request` from forks run in the fork context and do not have access to repository secrets (e.g. `SONAR_TOKEN`). By triggering SonarCloud from **all_green** via `workflow_run`, the SonarCloud job runs in the upstream repository context and can use the token.
- **Ordering**: SonarCloud runs only after `all_green` (including the coverage job) has finished, so coverage data is available when the scanner runs.

Flow:

1. PR or `push` triggers **`all_green`** (linters, sanity, units, coverage).
2. The **coverage** job runs `tox -e ansible2.20-py314-with_constraints`, finds `coverage.xml` under `.tox`, rewrites paths in the XML to be repo-relative, and uploads it as the `coverage` artifact.
3. When **`all_green`** completes successfully, the **SonarCloud** workflow is triggered.
4. The SonarCloud job checks out the repo at the run's commit, downloads the `coverage` artifact, sets `COVERAGE_PATHS`, and runs the scanner with `sonar.python.coverage.reportPaths` set so SonarCloud receives the coverage report.

### `all_green_check.yml`: coverage job

- **Trigger**: Same as `all_green` (`pull_request` and push to `main` and `stable-*`). The coverage job runs on every such run (linters/sanity only run on `pull_request`; units and coverage always run).
- **Steps**:
  1. Checkout repository.
  2. Set up Python 3.14 and install `tox`.
  3. Run `tox -e ansible2.20-py314-with_constraints` to execute unit tests and generate `coverage.xml` under `.tox`.
  4. **Rewrite coverage paths**: Locate `coverage.xml` under `.tox`, then replace the absolute path prefix (the `tox` env collection path) with an empty string so paths in the XML are repo-relative. This allows SonarCloud to match coverage to the repository layout when it checks out the same commit.
  5. Upload the rewritten `coverage.xml` as the artifact named `coverage`.
- **Gate**: The **`all_green`** job only succeeds when linters (on PRs), sanity (on PRs), units, and coverage all succeed (or are skipped where allowed).

### `sonarcloud.yml`: finalize job

- **Trigger**: `workflow_run` when the **`all_green`** workflow completes (success only).
- **Permissions**: `contents: read`, `pull-requests: read`, `actions: read` (needed to download artifacts from the triggering run).
- **Steps**:
  1. **Checkout** the repository at `workflow_run.head_sha`.
  2. **Download coverage artifacts** from the triggering all_green run using `dawidd6/action-download-artifact` (pinned by full commit SHA, v16 equivalent). Pattern: `coverage*`.
  3. **Set coverage report paths**: Run `find . -name "coverage*.xml"`, comma-separate the paths, and set `COVERAGE_PATHS` in the environment.
  4. **Get PR number and info** (when the triggering event was a pull_request): Use `gh pr list` and `gh api` to set `PR_NUMBER`, `PR_BASE`, and `PR_HEAD`.
  5. **Prepare SonarCloud args**: Set `sonar.scm.revision` to the commit SHA. For pull requests, add `sonar.pullrequest.key`, `sonar.pullrequest.branch`, and `sonar.pullrequest.base`. When `COVERAGE_PATHS` is set, add `sonar.python.coverage.reportPaths`.
  6. **SonarCloud Scan**: Run `SonarSource/sonarqube-scan-action@v7` with the prepared args and `SONAR_TOKEN` from repository secrets.

Coverage is only passed to the scanner when the download step finds at least one `coverage*.xml` file; otherwise the scan runs without coverage (and may rely on the default path in `sonar-project.properties` if no args override it).

## Summary

| Workflow | File | Trigger | Purpose |
|----------|------|---------|---------|
| `all_green` | `.github/workflows/all_green_check.yml` | `pull_request`, push to `main` and `stable-*` | Run linters, sanity, units, and coverage; gate on success |
| SonarCloud | `.github/workflows/sonarcloud.yml` | After `all_green` completes successfully | Download coverage from `all_green` run and run SonarScanner with PR or branch analysis |

| Artifact / config | Source | Use |
|-------------------|--------|-----|
| Coverage XML | `tox` (coverage job) → path rewrite → artifact `coverage` | Downloaded by SonarCloud job and passed as `sonar.python.coverage.reportPaths` |
| `sonar-project.properties` | Repository root | Project key, organization, sources, tests, exclusions, default coverage path, Python version, reference branch |
| `tox.ini` | Repository root | Defines testenv that runs `pytest` with `pytest-cov` and writes `coverage.xml` |
| `pyproject.toml` | Repository root | Pytest and coverage report options (`exclude_lines`, etc.); no SonarCloud-specific config |

## Debugging SonarCloud issues

If analysis fails or coverage is missing:

1. **Check `all_green`**: Ensure the `all_green` workflow (including the coverage job) succeeded for the same commit. SonarCloud downloads artifacts from that run.
2. **Check artifact**: In the SonarCloud run, confirm the "Download coverage artifacts" and "Set coverage report paths steps" found at least one `coverage*.xml` and set `COVERAGE_PATHS`.
3. **Run SonarScanner locally**: Install [SonarScanner CLI](https://docs.sonarsource.com/sonarqube-cloud/advanced-setup/ci-based-analysis/sonarscanner-cli/), set `SONAR_TOKEN` from [SonarCloud Security](https://sonarcloud.io/account/security), and run from the repo root:
   ```sh
   sonar-scanner -Dsonar.projectBaseDir=. -Dsonar.host.url=https://sonarcloud.io
   ```
   Fix any errors reported at the end of the output.

*Note:* Changes that break `sonar-project.properties` can still leave the PR status green because the SonarCloud workflow may not block the check. Use the SonarCloud project page and local `sonar-scanner` runs to verify configuration.

## References

- [SonarCloud Documentation](https://docs.sonarsource.com/sonarqube-cloud/)
- [GitHub Actions for SonarCloud](https://docs.sonarsource.com/sonarqube-cloud/advanced-setup/ci-based-analysis/github-actions-for-sonarcloud/)
- [Storing and sharing workflow data (artifacts)](https://docs.github.com/en/actions/writing-workflows/choosing-what-your-workflow-does/storing-and-sharing-data-from-a-workflow)
- [workflow_run event](https://docs.github.com/en/actions/writing-workflows/choosing-when-your-workflow-runs/events-that-trigger-workflows#workflow_run)
