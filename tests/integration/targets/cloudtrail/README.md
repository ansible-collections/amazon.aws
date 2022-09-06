# Cloudtrail integration test

This test-suite requires too much extra privileges and we cannot run the Cloudtrail interation tests in the CI.
Instead we run the test-suite offline with a recording of the last API interactions. This is way happen when
we call `./run.sh`.

If you introduce a change that require an update of the recording, you should call the `./record.sh` script.
This will refresh the `recording.tar.gz` tarball with the last API interactions.
