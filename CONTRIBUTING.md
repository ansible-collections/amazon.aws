# Contributing

## Getting Started

General information about setting up your Python environment, testing modules,
Ansible coding styles, and more can be found in the [Ansible Community Guide](
https://docs.ansible.com/ansible/latest/community/index.html).

Information about boto library usage, module utils, testing, and more can be
found in the [AWS Guidelines](https://docs.ansible.com/ansible/devel/dev_guide/platforms/aws_guidelines.html)
documentation.

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

## Pull Requests

All modules MUST have integration tests for new features. Upgrading to boto3 shall be considered a feature request.  
Bug fixes for modules that currently have integration tests SHOULD have tests added.  
New modules should be submitted to the [community.aws](https://github.com/ansible-collections/community.aws) collection
and MUST have integration tests.

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

For general information on running the integration tests see the
[Integration Tests page of the Module Development Guide](https://docs.ansible.com/ansible/devel/dev_guide/testing_integration.html#testing-integration),
especially the section on configuration for cloud tests.  For questions about writing tests the Ansible AWS community can
be found on Freenode IRC as detailed below.


### Code of Conduct
The `amazon.aws` collection follows the Ansible project's 
[Code of Conduct](https://docs.ansible.com/ansible/devel/community/code_of_conduct.html). 
Please read and familiarize yourself with this document.

### IRC
Our IRC channels may require you to register your nickname. If you receive an error when you connect, see 
[Freenode's Nickname Registration guide](https://freenode.net/kb/answer/registration) for instructions

The `#ansible-aws` channel on Freenode irc is the main and official place to discuss use and development
of the `amazon.aws` collection.
