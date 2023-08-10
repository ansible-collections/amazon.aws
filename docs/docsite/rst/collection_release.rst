:orphan:

.. _ansible_collections.amazon.aws.docsite.collection_release:

AWS collection release process
##############################

The ``amazon.aws`` and ``community.aws`` collections follow `semantic versioning <https://semver.org/>`_
with the `main branch <https://github.com/ansible-collections/amazon.aws/tree/main>`_ being the
pre-release or development branch, and separate ``stable`` branches used to backport patches for
release in minor and patch releases.  Please make sure you're familiar with semantic versioning
prior to preparing a release.

* Patch releases may **only** contain backwards compatible bug fixes.
* Minor releases must be backwards compatible, but may also include new functionality and
  deprecation announcements.
* Major releases may also include breaking changes.

Releases to `Ansible Galaxy <https://galaxy.ansible.com>`_ are automated through GitHub and Zuul
integrations.

Major releases
**************

.. note::
  The examples below will be based upon preparing the major release ``6.0.0``.  At the end of the
  process a new ``stable-6`` branch will have been created and the ``main`` branch will be ready for
  use as the ``7.0.0dev0`` development branch.

The major release process has two phases.

#. Preparing the branches
#. Generating the release

Preparing the branches involves creating a new ``stable`` branch, updating documentation links, and
bumping the version for the ``main`` branch.

Generating the release involves updating the version information, creating the changelog and
tagging the release.  This part of the process is identical to performing
`Minor and Patch releases<ansible_collections.amazon.aws.docsite.minor_releases>`
and will be covered in that section.

Pre-flight checks
=================

It's generally advisable to ask in the `Ansible + AWS Matrix chat room
<https://matrix.to/#/#aws:ansible.com>`_ prior to preparing a release to see if folks have any
patches that they'd like to get into a release.

Deprecations
------------

Prior to proceeding with a major release check that no ``collection-deprecated-version`` or
``ansible-deprecated-date`` entries exist in the
`sanity test ignore files <https://github.com/ansible-collections/amazon.aws/tree/main/tests/sanity>`_.

This generally involves changing a default or dropping support for something, however deprecations
are used as a warning for breaking changes.  Once a major version has been released breaking changes
should wait for the next major release before being applied.

In some cases it may be appropriate to either delay the change (update the deprecation version),
or abandon the deprecation.

Python and AWS SDK dependencies
-------------------------------

Starting with the 2.0.0 releases of ``amazon.aws`` and ``community.aws``, it is generally the
collection's policy to support the minor versions of ``botocore`` and ``boto3`` that were released
12 months prior to the most recent major collection release.  SDK support for Python versions also
drives which versions of Python the collections support.

SDK dependencies need to be updated in a number of places, primarily:

* README.md
* constraints.txt files (for our tests)
* ``ansible_collections.amazon.aws.plugins.module_utils.botocore.MINIMUM_BOTOCORE_VERSION``
* ``ansible_collections.amazon.aws.plugins.module_utils.botocore.MINIMUM_BOTO3_VERSION``

The pull request to update the SDK requirements can also include dropping explicit requirements for a
minimum ``boto3`` or ``botocore`` version in modules.  However, dropping code that maintains
backwards compatible support for an older SDK version would be a breaking change and must not be
backported.

For an example see `ansible-collections/amazon.aws#1342 <https://github.com/ansible-collections/amazon.aws/pull/1342>`_

Preparing the branches
======================

Ensure that your local copy of the ``main`` branch is up to date and contains all planned patches.

Preparing a new stable branch
-----------------------------

.. warning::
  Zuul will need updating here too.

  As part of the next release cycle please add an entry here about configuring the Zuul sanity jobs
  for the new stable-6 branch.

Create and push a new ``stable-<major-version>`` branch (for example ``stable-6`` for release
``6.0.0``):

.. code-block:: bash

  git fetch origin
  git checkout main
  git reset --hard origin/main
  git checkout -b stable-6
  git push --set-upstream origin stable-6

Create a pull request against the new branch updating any documentation links from ``main`` to the
new ``stable-<major-version>`` branch.

For an example pull request see
`ansible-collections/amazon.aws#1107 <https://github.com/ansible-collections/amazon.aws/pull/1107>`_

Updating main
-------------

Now that our new major release has been branched, we update the ``main`` branch so that it's
configured as the pre-release development version for the **next** release (for example
``7.0.0-dev0`` if you're preparing ``6.0.0``).

Create a pull request against the ``main`` branch updating the
`galaxy.yml <https://github.com/ansible-collections/amazon.aws/blob/main/galaxy.yml>`_ version
information and the  `plugins/module_utils/common.py
<https://github.com/ansible-collections/amazon.aws/blob/main/plugins/module_utils/common.py>`_
version information to a ``dev0`` prerelease of the next major release.  This may result in deprecation
errors from the sanity tests.  Create issues and add entries to the relevant
`sanity test ignore files <https://github.com/ansible-collections/amazon.aws/tree/main/tests/sanity>`_.
(including a link to the issue)

For an example pull request see
`ansible-collections/amazon.aws#1108 <https://github.com/ansible-collections/amazon.aws/pull/1108>`_


Next steps
----------

Once these pull requests have been merged there should be a new ``stable`` branch for the release
series (for example ``stable-6`` for all ``6.x.y`` releases) and the ``main`` branch should have
been updated.  After which you can continue the major release process by following the steps for
`Minor and Patch releases<ansible_collections.amazon.aws.docsite.minor_releases>`.


.. _ansible_collections.amazon.aws.docsite.minor_releases:

Minor and Patch releases
************************

.. note::

  The examples below will be based upon preparing the major release ``6.0.0`` using the ``stable-6``
  branch.  While ``6.0.0`` is a major release, this part of the process is identical for major,
  minor and patch releases.

Ensure that the relevant stable branch (for example ``stable-6``) is up to date and includes all
planned patches.  If you have local copies of both ``amazon.aws`` and ``community.aws`` it is
strongly recommended that you checkout the same branch for both collections.

Outline of steps for generating a release:

#. Create a local branch
#. Update version information
#. Generate the changelog
#. Generate (and merge) the PR
#. Tag the release
#. Announce the release

Create a working branch for your release
========================================

Checkout the relevant stable branch, and create a local working branch for the release.

.. code-block:: bash

  git fetch origin
  git checkout stable-6
  git reset --hard origin/stable-6
  git checkout -b release/6.0.0/prepare


Update version information
==========================

We need to update the version information in a couple of places:

* galaxy.yml
* plugins/module_utils/common.py

In your local clone of the repository, update ``galaxy.yml`` with the new release version
information.

**galaxy.yml:**

.. code-block:: yaml

  namespace: amazon
  name: aws
  version: 6.0.0
  ...

**plugins/module_utils/common.py:**

.. code-block:: python

   AMAZON_AWS_COLLECTION_VERSION = "6.0.0"

.. note::

  Separately committing each of the changes to your local branch as you go will save you time if
  there are problems with changelog fragments.

  While the sanity tests can pick up invalid YAML and RST, they don't detect broken links
  prior to the final changelog generation.

Generate the Changelogs
=======================

Install Antsibull
-----------------

We use `antsibull-changelog <https://github.com/ansible-community/antsibull-changelog>`_ to generate
our changelogs from the fragments, and `antsibull-docs
<https://github.com/ansible-community/antsibull-docs>`_ to generate the `rendered documentation.
<https://ansible-collections.github.io/amazon.aws/branch/main/collections/amazon/aws/index.html>`_

If you've not already installed these tools then you'll need to do so (this can be done in a virtual
environment if desired):

.. code-block:: bash

   pip install ansible sphinx-ansible-theme antsibull-changelog antsibull-docs

Add a release_summary changelog fragment
----------------------------------------

While not strictly necessary it's preferable to add a release summary that will be added to the
changelog.  For example, the `release summary for 5.2.0
<https://ansible-collections.github.io/amazon.aws/branch/stable-5/collections/amazon/aws/docsite/CHANGELOG.html#release-summary>`_

**changelogs/fragments/release-summary.yml:**

.. code-block:: yaml

  release_summary: |
    Add a short description highlighting some of the key changes in the release.

Commit the release summary to your local branch.

Generate the merged changelog
-----------------------------

Next we need to generate the merged changelog.  This will automatically delete the used fragments,
update ``CHANGELOG.rst``, ``changelogs/changelog.yaml``, and ``git add`` what it changes.

.. code-block:: bash

  antsibull-changelog release

Commit all of these changes to your local branch.

Create your Pull Request
------------------------

Once everything's been committed locally you can prepare a pull request.  The pull request should be
for the relevant ``stable`` branch and **not** the ``main`` branch.

All tests for the PR should pass prior to merging.  This pull request can be approved and merged as
usual.

Because ``CHANGELOG.rst`` is actually generated from ``changelogs/changelog.yaml``, if you need to
fix issues with a changelog fragment, the easiest option is to revert the final changelog
generation, fix the original fragment, and re-generate the final changelog (This is why you should
commit small changes as you go).

.. note::

  Releases for amazon.aws should either be prepared by someone from the Ansible Cloud Content
  team, or be approved by at least one person from the Ansible Cloud Content team.

.. warning::

  Prior to triggering the merge for the release pull request, please warn the `Ansible + AWS Matrix
  chat room <https://matrix.to/#/#aws:ansible.com>`_ the final tagging (which releases the code to
  `Ansible Galaxy <https://galaxy.ansible.com>`_) should be done using the pull request commit.

Tag the release
===============

Pushing the release to `Ansible Galaxy <https://galaxy.ansible.com>`_ is performed by Zuul.  When
a tag is pushed GitHub Zuul will automatically build the relevant artifacts and push them to Galaxy.

.. code-block:: bash

  git fetch origin
  git checkout stable-6
  git reset --hard origin/stable-6
  git tag 6.0.0
  git push origin 6.0.0


Announce the release
====================

Bullhorn
--------

The Bullhorn is a newsletter for the Ansible developer community.  If you have anything to share
about what you've been up to with Ansible lately, including new collection releases, simply hop
into `#social:ansible.com <https://matrix.to/#/#social:ansible.com>`_ (the Ansible Social room on
Matrix) and leave a message, tagging newsbot.  Your update will then be included in the next
edition of the Bullhorn (pending editor approval).

For more information (and some examples) see the `Ansible News Working Group wiki page
<https://github.com/ansible/community/wiki/News#the-bullhorn>`_

.. warning::
  As part of the next release cycle please add an example here.

.. .. code-block:: none
..
..   @newsbot [amazon.aws 6.0.0](https://github.com/ansible-collections/amazon.aws/tree/6.0.0) has been released.
     This is a major release, and includes XXX WRITE ME XXX
     [see changelog for more details](https://github.com/ansible-collections/amazon.aws/blob/6.0.0/CHANGELOG.rst)

Update the chat room topic
--------------------------

Once the release is available from Ansible Galaxy, the topic should be updated in the
`Ansible + AWS Matrix chat room. <https://matrix.to/#/#aws:ansible.com>`_  This generally requires
assistance from a member of Ansible staff.

Create a GitHub "Release"
-------------------------

While the AWS collections are generally distributed via Ansible Galaxy, for visibility we also
create a GitHub release.  Pushing a tag should automatically do this, however, should the automation
fail, releases can also be created manually.

Copy the release notes from the rendered changelog file and generate a GitHub release based upon the
newly created tag.

* `amazon.aws <https://github.com/ansible-collections/amazon.aws/releases>`_
* `community.aws <https://github.com/ansible-collections/community.aws/releases>`_

.. note::
  For more information see: `Managing releases in a repository
  <https://docs.github.com/en/repositories/releasing-projects-on-github/managing-releases-in-a-repository>`_

Cleanup
*******

We usually forward-port the changelog entries.  If multiple releases are planned concurrently then
the changelog entries can be merged into the ``main`` branch in a single PR.

.. code-block:: bash

  git fetch origin --tags
  git checkout main
  git reset --hard origin/main
  git checkout -b release/6.0.0/changelog-to-main
  git cherry-pick -n 6.0.0
  git checkout origin/main galaxy.yml
  git commit -m "Add changelogs from release 6.0.0 to main"

.. note::

  To improve visibility of collection-wide deprecations, such as pending changes to module_utils,
  or deprecated support for a version of Python, the corresponding changelog fragment can be kept in
  the main branch.  This will ensure that there is also a deprecation warning in the next major
  release.
  Keeping a fragment can be done by using git to checkout the original fragment prior to
  commiting and pushing:
  ``git checkout origin/main changelogs/fragments/<some fragment>.yml``

.. warning::

  Any conflicts will need to be resolved prior to commiting.

.. warning::

  Be careful not to update galaxy.yml when you're forward-porting the changelog entries.
