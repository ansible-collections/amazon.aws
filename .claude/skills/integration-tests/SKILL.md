---
name: integration-tests
description: Run integration tests for modules and plugins
---

<!--
This skill runs integration tests using ansible-test. Integration tests are in
tests/integration/targets/ and test actual functionality against real AWS resources
or mocked services.
-->

# Integration Tests Workflow

Run integration tests for specific modules or targets:

## Finding the Test Target

1. **If user provides a test name**: Use it directly (e.g., `ec2_instance`, `connection_aws_ssm_amazon`)

2. **If user provides a file path**, determine the test name:

   **For modules** (`plugins/modules/<name>.py`):
   - Test is usually: `<name>`
   - Example: `plugins/modules/ec2_instance.py` → test: `ec2_instance`

   **For inventory plugins** (`plugins/inventory/<name>.py`):
   - Test is: `inventory_<name>`
   - Example: `plugins/inventory/aws_ec2.py` → test: `inventory_aws_ec2`

   **For lookup plugins** (`plugins/lookup/<name>.py`):
   - Test is: `lookup_<name>`
   - Example: `plugins/lookup/aws_account_attribute.py` → test: `lookup_aws_account_attribute`

   **For callback plugins** (`plugins/callback/<name>.py`):
   - Test is: `callback_<name>`
   - Example: `plugins/callback/aws_resource_actions.py` → test: `callback_aws_resource_actions`

   **For connection plugins** (`plugins/connection/<name>.py`):
   - Test is usually: `connection_<name>_<os_variant>`
   - Example: `plugins/connection/aws_ssm.py` has multiple tests:
     - `connection_aws_ssm_amazon`
     - `connection_aws_ssm_centos`
     - `connection_aws_ssm_windows`
     - etc.

3. **If test directory doesn't exist**, search for aliases:
   ```bash
   grep -r "^<module_name>$" tests/integration/targets/*/aliases
   ```
   - This shows which test directory contains the module as an alias
   - Example: `cloudformation_info` is tested by the `cloudformation` target
   - Example: `autoscaling_group_info` is tested by the `autoscaling_group` target

4. **If user just says "run integration tests"**:
   - Check git diff to see what modules/plugins changed
   - Find corresponding tests for those files
   - Ask user which tests to run

## Running the Tests

5. **Execute ansible-test**:
   ```bash
   ansible-test integration --docker default --allow-unstable <test-name>
   ```

   **Flags explained**:
   - `--docker default`: Run in a Docker container with default image
   - `--allow-unstable`: Allow tests with "unstable" alias to run (used when updating shared code/dependencies where one unstable test shouldn't block all testing)
   - Add `--color` for colored output if logging to a file

6. **Optional: Save output to log file**:
   - If user requests logging or if test name suggests it (connection tests, etc.)
   - Use: `ansible-test integration --docker default --allow-unstable --color <test-name> 2>&1 | tee <test-name>.log`
   - Log files help with debugging complex failures

7. **Monitor progress**:
   - Integration tests can take 10-30 minutes depending on the target
   - Show the ansible-test command being run
   - Stream output as it runs (don't buffer)

## Understanding Test Results

8. **Analyze failures**:
   - Integration test failures often indicate:
     - Real AWS API issues (rate limiting, permissions)
     - Test infrastructure problems
     - Actual bugs in the module
   - Check the error messages for:
     - AWS API errors (throttling, credentials, permissions)
     - Test setup failures (missing resources)
     - Assertion failures (actual bugs)

9. **Report results**:
   - Number of tests passed/failed
   - Which specific tasks failed
   - Error messages from failures
   - Suggestion: Re-run if it looks like transient AWS issues

## Important Notes

- **AWS credentials**: Integration tests require valid AWS credentials and will create/delete real resources
- **Time estimates**: Tests have estimated durations in their `aliases` file (e.g., `time=30m`) used by CI for test distribution
- **Test isolation**: Each test should clean up its own resources
- **Docker required**: Tests run in Docker containers by default
- **Multiple tests**: Can specify multiple targets: `ansible-test integration --docker default --allow-unstable test1 test2`
- **Unstable tests**: Tests marked with "unstable" alias may fail intermittently; `--allow-unstable` allows them to run

## Common Test Targets

- **Module tests**: Named after the module (e.g., `ec2_instance`, `s3_bucket`)
- **Inventory tests**: Prefixed with `inventory_` (e.g., `inventory_aws_ec2`)
- **Lookup tests**: Prefixed with `lookup_` (e.g., `lookup_aws_account_attribute`)
- **Callback tests**: Prefixed with `callback_` (e.g., `callback_aws_resource_actions`)
- **Connection tests**: Prefixed with `connection_` and include OS variant (e.g., `connection_aws_ssm_amazon`)
- **Info module tests**: Often included as aliases in the main module test

## Example Usage

**Run test for ec2_instance module**:
```bash
ansible-test integration --docker default --allow-unstable ec2_instance
```

**Run test for aws_ec2 inventory plugin**:
```bash
ansible-test integration --docker default --allow-unstable inventory_aws_ec2
```

**Run test for lookup plugin**:
```bash
ansible-test integration --docker default --allow-unstable lookup_aws_account_attribute
```

**Run connection tests**:
```bash
ansible-test integration --docker default --allow-unstable connection_aws_ssm_amazon
```

**Run multiple related tests**:
```bash
ansible-test integration --docker default --allow-unstable s3_bucket s3_object
```

**Run with logging**:
```bash
ansible-test integration --docker default --allow-unstable --color ec2_instance 2>&1 | tee ec2_instance.log
```
