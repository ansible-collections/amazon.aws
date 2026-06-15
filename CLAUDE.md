

<!-- lola:instructions:start -->
<!-- lola:module:ai-forge:start -->
# Ansible Collection Development

Module provides skills and commands for Ansible collection development workflows including commits, PRs, releases, testing, and security scanning.

## Agent Roles

This module defines specialized agent roles for Ansible content development. Each role has specific capabilities, scope, and constraints.

### Module Developer Agent

**Purpose**: Implement and maintain Ansible modules and plugins.

**Scope**: `plugins/modules/`, `plugins/module_utils/`, `plugins/action/`, `plugins/lookup/`, `plugins/filter/`

**Context Files**:

- `CLAUDE.md`, `AGENTS.md`, or project documentation
- Module documentation standards
- Existing modules for patterns

**Capabilities**:

- Write new modules following Ansible conventions
- Refactor existing module code
- Implement module_utils shared code
- Add argument specs and documentation

**Constraints**:

- Must follow architectural invariants (see below)
- Must include DOCUMENTATION, EXAMPLES, RETURN blocks
- Must use `module.fail_json()` for errors, never bare `raise`
- Must set `no_log=True` for sensitive parameters

---

### Test Agent

**Purpose**: Write and run tests using ansible-test.

**Scope**: `tests/unit/`, `tests/integration/`, `tests/sanity/`

**Context Files**:

- ansible-test documentation
- Existing test patterns in the collection
- CI workflow configuration

**Capabilities**:

- Write unit tests for module_utils
- Write integration tests for modules
- Run sanity, unit, and integration tests
- Analyze test failures and suggest fixes

**Constraints**:

- Integration tests must be idempotent (run twice, second is `changed=false`)
- Must include both success and failure test cases
- Must clean up any resources created during tests

---

### Release Agent

**Purpose**: Handle releases and changelog management.

**Scope**: `changelogs/`, `galaxy.yml`, `CHANGELOG.rst`

**Context Files**:

- Release process documentation
- antsibull-changelog configuration
- Previous release patterns

**Capabilities**:

- Create changelog fragments
- Generate changelogs using antsibull-changelog
- Update galaxy.yml version
- Tag releases and create GitHub releases

**Constraints**:

- Must follow SemVer for version numbering
- Must include changelog fragment for every user-facing change
- Must verify all tests pass before release

---

### Review Agent

**Purpose**: Review PRs and code quality.

**Scope**: All files (read-only analysis)

**Context Files**:

- Ansible Collection Review Checklist
- Red Hat CoP automation good practices
- Project-specific CLAUDE.md

**Capabilities**:

- Review code against best practices
- Check for security issues
- Verify documentation completeness
- Assess test coverage

**Constraints**:

- Read-only analysis, does not modify files
- Must provide actionable feedback
- Must distinguish blockers from suggestions

---

### CI/CD Agent

**Purpose**: Maintain CI pipelines and automation.

**Scope**: `.github/workflows/`, `.gitlab-ci.yml`, `tox.ini`

**Context Files**:

- CI/CD best practices
- ansible-test CI patterns
- Security scanning requirements

**Capabilities**:

- Create and update CI workflows
- Configure test matrices
- Set up security scanning
- Optimize CI performance

**Constraints**:

- Must pin GitHub Actions to commit SHAs
- Must not expose secrets in logs
- Must include all required test types (sanity, unit, integration)

---

## Architectural Invariants

These are non-negotiable rules for Ansible collection development. Violating any will cause issues.

1. **Modules must be idempotent** — Repeated runs with same parameters produce same state with `changed=False`

2. **No shell=True with user input** — Prevents command injection; use `module.run_command()` with list arguments

3. **All parameters documented** — DOCUMENTATION block must include description, type, and required/default for every parameter

4. **Sensitive parameters use no_log=True** — Passwords, tokens, API keys, and secrets must never appear in logs

5. **Errors use module.fail_json()** — No bare `raise`, `sys.exit()`, or unhandled exceptions

6. **Use FQCNs in examples** — `community.general.module_name`, not just `module_name`

7. **Return values documented** — RETURN block must describe all keys returned by the module

8. **Check mode supported where applicable** — Set `supports_check_mode=True` and handle accordingly

9. **No hardcoded credentials** — Use environment variables, Ansible Vault, or credential plugins

10. **Changelog fragments required** — Every user-facing change needs a changelog fragment

---

## Quality Gates

Before completing any task, verify:

- [ ] `ansible-test sanity` passes
- [ ] `ansible-lint` passes
- [ ] Unit tests pass (if applicable)
- [ ] Integration tests pass (if applicable)
- [ ] Changelog fragment created (for user-facing changes)
- [ ] Documentation updated
- [ ] No security issues introduced

---

## Handoff Protocol

When transitioning between agent roles:

**Completing Agent**:

- Document what was done
- Note any deviations from the plan
- List open questions for the next agent
- Verify no architectural invariants were violated

**Receiving Agent**:

- Read CLAUDE.md for project context
- Read relevant skill documentation
- Check for notes from previous agent
- Continue from documented state

---

## When to Use

### Commands

- **/check-pr-actions command**: Use the `/check-pr-actions` command to check GitHub Actions or GitLab CI status for the current pull request or branch.
  Analyzes failures by examining logs, identifying patterns across matrix tests, and suggesting specific fixes.
  Invoke when asked to check PR status, CI status, "why is the PR failing?", or to troubleshoot GitHub Actions/GitLab CI failures.

- **/check-pr-sonarcloud command**: Use the `/check-pr-sonarcloud` command to check SonarCloud static analysis results for the current pull request.
  Uses get-pr-number to detect the PR and sonarcloud-remediation to fetch and analyze PR-specific issues.
  Invoke when asked to check SonarCloud for the PR, review static analysis results, or see what code quality issues affect the current PR.

- **/setup-python-venv command**: Use the `/setup-python-venv` command to create, validate, or remove a
  project-local Python virtual environment. Uses the `python-virtual-env` skill.
  Invoke when asked to set up a venv, local Python dev environment, or validate `.venv` before pip installs.

### Skills

- **commit skill**: Use the `commit` skill when you want to create a conventional commit
  with FQCN scopes for Ansible collection content.
  Invoke when the user asks to "commit", "create a commit", or "git commit".

- **configure-sonarcloud-collection skill**: Use the `configure-sonarcloud-collection` skill to add
  SonarCloud (SonarQube Cloud) to a collection repository: `sonar-project.properties`, GitHub Actions
  workflow with org `SONAR_TOKEN`, XML coverage at the repo root for Sonar, and README or dedicated docs.
  The skill includes fork/secret safety and assistant-safe patterns (see Security section inside the
  skill). Invoke when asked to set up, onboard, or configure SonarCloud/SonarQube analysis for
  a collection, wire CI for the scanner, or add coverage.xml for Sonar.

- **configure-sonarcloud-coverage skill**: Use the `configure-sonarcloud-coverage` skill for the **second phase**
  of SonarCloud setup: CI jobs that emit XML coverage, passing `sonar.python.coverage.reportPaths` to the
  scanner, optional `workflow_run` + artifact flows or reusable **`workflow_call`** Sonar (as in public amazon.aws coverage PRs), aggregator
  workflows, and README or docs badges. Invoke when Sonar already runs but coverage is missing or when the
  user asks to mirror amazon.aws-style coverage integration after initial Sonar onboarding.

- **sonarcloud-workflow-templates** (under `module/skills/`): Canonical Sonar workflow and properties
  templates for the **ansible-collections** GitHub org. Not a standalone skill.
- Before copying files into a collection repo, read **`sonarcloud-workflow-templates/README.md`** in this
  module.
- That README compares **`workflow_run`** vs **`workflow_call`**, documents aggregator **`name: all_green`**,
  and explains **`coverage*`** artifact patterns vs a single artifact named **`coverage`**. For **`workflow_call`**,
  also use **`all_green-caller.sonarcloud-job.yml.template`** for the **`sonarcloud`** job in **`all_green_check.yaml`**
  (explicit **`secrets:`**); live reference: **kubernetes.core** [PR #1124](https://github.com/ansible-collections/kubernetes.core/pull/1124).

- **changelog-fragment skill**: Use the `changelog-fragment` skill to create or update changelog fragments for documenting changes.
  Supports automatic change analysis and PR URL updates.
  Invoke when asked to create a changelog fragment, add a fragment, or update fragments with PR URLs.

- **create-branch skill**: Use the `create-branch` skill to create a new feature branch following project conventions.
  Fetches latest from origin, bases branch off origin/main, and unsets upstream for fork workflows.
  Invoke when asked to create a branch, start new work, or "create a branch for...".

- **create-pr skill**: Use the `create-pr` skill to create a draft pull request with pre-flight checks, changelog validation, and automated formatting.
  Performs branch validation, checks for changelog fragments, optionally runs tests, analyzes changes to suggest PR details, and updates fragments with PR number.
  Invoke when asked to "create a PR", "make a pull request", or "open a PR".

- **pr-review skill**: Use the `pr-review` skill to review pull requests and code changes
  against project standards and the Ansible Collection Review Checklist.
  Invoke when asked to review a PR, patch, diff, or set of code changes.

- **remove-deprecations skill**: Use the `remove-deprecations` skill to find and remediate overdue deprecation warnings.
  Identifies deprecated code past removal date/version, categorizes by priority, and guides implementation of removal changes.
  Invoke when preparing for releases, cleaning up technical debt, or when asked to remove deprecations.

- **release skill**: Use the `release` skill to guide the release of an Ansible collection.
  Automatically determines the next version from changelog fragments
  and outputs step-by-step instructions.
  Invoke when asked to release, publish, or tag a new collection version.

- **run-tests skill**: Use the `run-tests` skill to run or write sanity, unit, and integration tests using `ansible-test`. Invoke when asked to run, check, or write tests for a module or utility.

- **security-scan skill**: Use the `security-scan` skill to scan the collection for security vulnerabilities, hardcoded secrets, and compromised dependencies.
  Checks Python dependencies, GitHub Actions, and code for security issues.
  Invoke when asked to scan for vulnerabilities, audit security, check for secrets, or before releases.

- **sonarcloud-remediation skill**: Use the `sonarcloud-remediation` skill to fetch, analyze, and fix SonarCloud issues with end-to-end automation.
  Supports both project-wide debt reduction and PR-specific quality gates. Phase A analyzes and groups issues by rule and module with priority sorting.
  Phase B applies fixes with validation gates, batching, and strategic approval checkpoints.
  Invoke when asked to check, review, analyze, or fix SonarCloud results, code smells, security hotspots, or static analysis findings.

- **next-release skill**: Use the `next-release` skill to calculate next patch/minor/major release versions following SemVer.
  Invoke when asked what version to use for version_added tags or about next release versions.

- **python-virtual-env skill**: Use the `python-virtual-env` skill to create or validate a project-local
  Python virtual environment for isolated pip installs and local tooling.
  Typically invoked by the `/setup-python-venv` command; also use directly when setting up local Python
  dev, installing Python dependencies with pip, or before non-Docker Python commands.
  Do not use for `ansible-test --docker` workflows unless the user explicitly wants a local venv.

### Utility Skills

- **current-release skill**: Helper skill that fetches the current release version from git tags/branches or galaxy.yml. Used internally by other skills.

- **get-branch-changes skill**: Helper skill that determines merge-base and changed files for the current branch, avoiding inclusion of unrelated changes when branch is behind target.
  Used internally by changelog-fragment and create-pr skills.

- **get-pr-action-results skill**: Helper skill that gets GitHub Actions/GitLab CI results for a pull request or branch, analyzes failures, and suggests fixes.
  Used internally by check-pr-actions command and other workflows.

- **get-pr-number skill**: Helper skill that determines the pull request number for a branch. Used internally by other skills.

- **get-pr-zuul-results skill**: Helper skill that gets Zuul CI build status and log URLs for a pull request in ansible-collections repositories.
  Used internally by other skills and workflows that need to check Zuul CI status.

- **get-upstream-info skill**: Helper skill that determines upstream repository information and service identifiers (GitHub/GitLab). Used internally by other skills.

## Configuration

**Optional Dependencies:**

- `antsibull-changelog` - Used for changelog generation
- `gh` CLI - Used for GitHub/GitLab operations (PRs, releases, upstream detection)
- `ansible-test` - Used for running sanity, unit, and integration tests
- `curl` - Used for fetching SonarCloud analysis results
- `pip-audit` or `safety` - Used for Python dependency security scanning
- `gitleaks` - Used for secret detection

**Required Context:**

- The collection must reside at `ansible_collections/<namespace>/<name>/` (relative to a directory on `ANSIBLE_COLLECTIONS_PATHS`) for imports to resolve correctly
- Collection identity (namespace, name, version) is read from `galaxy.yml`

## Notes

- All skills follow Ansible collection conventions and best practices
- The commit skill uses Conventional Commits 1.0.0 standard
- The changelog-fragment skill supports two modes: creating new fragments and updating existing fragments with PR URLs
- The release skill includes human confirmation gates at critical steps
- The pr-review skill produces structured reports with blockers/warnings/suggestions and a verdict
- The security-scan skill can be integrated into CI/CD pipelines for automated security checks

## References

- [Ansible Collection Development Guide](https://docs.ansible.com/ansible/latest/dev_guide/developing_collections.html)
- [Red Hat CoP Automation Good Practices](https://github.com/redhat-cop/automation-good-practices)
- [Ansible Collection Review Checklist](https://docs.ansible.com/ansible/latest/community/collection_contributors/collection_reviewing.html)
- Pattern inspired by [ansible/apme](https://github.com/ansible/apme) agent architecture
<!-- lola:module:ai-forge:end -->

<!-- lola:module:ansible-role:start -->
# Ansible Role

Module provides commands for scaffolding Ansible roles following Red Hat CoP automation good practices.

## When to Use

- **ansible-scaffold-role command**: Use `/ansible-scaffold-role` to create a new Ansible role that fully complies with Red Hat CoP good practices. Features include:
  - Interactive variable builder that asks what the role manages (packages, services, configs, users, firewall, storage) and generates realistic defaults, tasks,
    handlers, and templates
  - Task componentization that splits complex roles into install.yml, configure.yml, service.yml with proper sub-task name prefixes
  - Smart handler generation that creates actual handlers (restart, reload, validate) based on role purpose
  - Collection-aware scaffolding using ansible-creator inside collections with fallback to manual creation
  - Standalone role creation for roles outside collections

## Configuration

**Optional Dependencies:**

- `ansible-creator` CLI - Used to generate role skeleton structure (falls back to manual creation if not installed)

**Required Context:**

- CoP rules from `CLAUDE.md` and `redhat-cop-automation-good-practices-*.md` files
- Fallback to https://github.com/redhat-cop/automation-good-practices when rules not available locally

## Notes

- The scaffold command follows an interactive pattern: gather user input about what the role manages, then generates appropriate variables, tasks, handlers,
  and templates pre-populated with realistic content
- All generated roles include proper meta/argument_specs.yml, README.md with examples, and CoP-compliant variable naming
- Roles are validated post-scaffold to ensure compliance with all CoP rules (no dashes in names, FQCN module usage, proper YAML formatting, etc.)
<!-- lola:module:ansible-role:end -->
<!-- lola:instructions:end -->
