## Fake integration suite

This is a fake integration suite including an aliases file listing every module name with missing integration tests (some of them are covered by units). 

This fake suite is necessary for the new CI ansible-test-splitter behaviour. Namely, if one of the modules (listed in the aliases file) without a test suite is modified, the CI is run for the entire collection since the ansible-test-splitter won't find any target match. This fake integration suite helps handle this situation by avoiding running the CI for the whole collection. Furthermore, since the modules listed in the aliases file are marked as disabled, tests are automatically skipped.