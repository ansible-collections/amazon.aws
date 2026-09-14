# -*- coding: utf-8 -*-
# Copyright: Contributors to the Ansible project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

"""Contract tests for the indirect-node audit query file.

The query file in ``extensions/audit/`` is executable code that runs inside the
Automation Platform controller, and its output feeds subscription node counting.
Nothing else in this repository executes it, so a change to it ships with a green
CI run no matter what it does.

These tests assert the contract that ``awx/main/tasks/host_indirect.py`` actually
imposes -- not the output the query happens to produce today. That distinction is
the whole point: an assertion captured from real output agrees with that output
by construction, so it can only detect drift, never wrongness.

The contract, read off the consumer:

* ``name``            must be present and must never be null.
                      ``if name is None: continue``
* ``canonical_facts`` must be present and truthy.
                      ``if not data.get('canonical_facts'): continue``
* ``canonical_facts`` must contain no null at any depth. ``get_hashable_form()``
                      accepts int/float/str/bool/dict/list/tuple and raises
                      ``UnhashableFacts`` on anything else, including ``None``;
                      the caller catches it and skips the record. One null in one
                      field silently discards the whole node.
* ``canonical_facts`` is the *sole* dedup key -- ``results[hashable_facts]``. It
                      must therefore hold identity and nothing else. A mutable
                      field in it re-counts the same node every time it changes.
* ``facts``           must carry ``infra_type``, ``infra_bucket`` and
                      ``device_type``, normalised ``lowercase_with_underscores``.
                      A node without them is counted but cannot be bucketed, so
                      it is invisible in every rollup.

These are static checks over the query source. They need no credentials, no live
endpoint and no recorded fixture, so they run in ``ansible-test units`` on every
change and cannot be skipped by path filtering.
"""

from __future__ import absolute_import, division, print_function

__metaclass__ = type

import os
import re

import pytest
import yaml

# --------------------------------------------------------------------------
# Locate the query file
# --------------------------------------------------------------------------

COLLECTION_ROOT = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..", "..", "..")
)
AUDIT_DIR = os.path.join(COLLECTION_ROOT, "extensions", "audit")
QUERY_FILE = os.path.join(AUDIT_DIR, "event_query.yml")

NORMALIZED = re.compile(r"^[a-z0-9]+(_[a-z0-9]+)*$")
TAXONOMY_KEYS = ("infra_type", "infra_bucket", "device_type")

# Field names that change over the life of a node. Anything here inside
# canonical_facts is an overcount: the same node is re-counted as a new one
# every time the value changes. These belong in `facts`, which is not hashed.
VOLATILE_KEYS = frozenset([
    "status", "state", "tags", "hostname", "ip", "ipv4", "ipv6", "lanip",
    "lan_ip", "mac", "management_ip", "managementip", "interface_ip",
    "interfaceip", "address", "power_state", "powerstate", "role", "version",
    "firmware",
])

# Stable identifiers. A display name alongside one of these is redundant and
# mutable -- renaming the object produces a second audit row for one node.
IDENTITY_KEYS = frozenset([
    "id", "moid", "serial", "serial_number", "object_guid", "guid", "uuid",
    "ansible_product_serial", "instance_id", "arn",
])

# Human-facing labels. Not volatile enough to reject on their own -- for some
# resources a name is the only identity there is -- but redundant and harmful
# next to a stable identifier.
DISPLAY_NAME_KEYS = frozenset(["name", "host_name", "hostname", "display_name"])


def load_queries():
    with open(QUERY_FILE) as handle:
        document = yaml.safe_load(handle) or {}
    return {
        key: (value["query"] if isinstance(value, dict) else value)
        for key, value in document.items()
    }


QUERIES = load_queries()
MODULES = sorted(QUERIES)


# --------------------------------------------------------------------------
# Minimal jq source handling -- brace matching, not a parser. Enough to find
# two object literals and enumerate their value expressions.
# --------------------------------------------------------------------------

def strip_comments(source):
    lines = []
    for line in source.splitlines():
        in_string = False
        for index, char in enumerate(line):
            if char == '"':
                in_string = not in_string
            elif char == "#" and not in_string:
                line = line[:index]
                break
        lines.append(line)
    return "\n".join(lines)


def balanced_block(source, start=0):
    """Return the ``{...}`` block beginning at the first brace at or after start."""
    open_at = source.find("{", start)
    if open_at < 0:
        return None, -1
    depth = 0
    in_string = False
    index = open_at
    while index < len(source):
        char = source[index]
        if in_string:
            if char == "\\":
                index += 2
                continue
            if char == '"':
                in_string = False
        elif char == '"':
            in_string = True
        elif char == "{":
            depth += 1
        elif char == "}":
            depth -= 1
            if depth == 0:
                return source[open_at:index + 1], index
        index += 1
    return source[open_at:], len(source)


def split_pairs(block):
    """Split a jq object literal into ``(key, value-expression)`` pairs."""
    body = block[1:-1]
    parts = []
    depth = 0
    in_string = False
    buffer_ = []
    for char in body:
        if in_string:
            buffer_.append(char)
            if char == '"':
                in_string = False
            continue
        if char == '"':
            in_string = True
        elif char in "{[(":
            depth += 1
        elif char in "}])":
            depth -= 1
        elif char == "," and depth == 0:
            parts.append("".join(buffer_))
            buffer_ = []
            continue
        buffer_.append(char)
    parts.append("".join(buffer_))

    pairs = []
    for part in parts:
        part = part.strip()
        if not part:
            continue
        depth = 0
        in_string = False
        cut = -1
        for index, char in enumerate(part):
            if in_string:
                if char == '"':
                    in_string = False
                continue
            if char == '"':
                in_string = True
            elif char in "{[(":
                depth += 1
            elif char in "}])":
                depth -= 1
            elif char == ":" and depth == 0:
                cut = index
                break
        if cut < 0:
            pairs.append((part.strip('"'), None))
        else:
            pairs.append((part[:cut].strip().strip('"'), part[cut + 1:].strip()))
    return pairs


def emitted_record(query):
    """The object the query emits: the last balanced block mentioning canonical_facts."""
    source = strip_comments(query)
    position = 0
    found = None
    while True:
        block, end = balanced_block(source, position)
        if block is None:
            break
        if "canonical_facts" in block:
            found = block
        position = end + 1
    return found


def sub_object(expression):
    block = balanced_block(expression or "", 0)[0]
    return dict(split_pairs(block)) if block else {}


READERS = re.compile(r"\b(?:test|match|capture|contains|split|startswith"
                     r"|endswith|ltrimstr|rtrimstr|sub|gsub|inside)\s*\(")


def strip_reader_calls(expression):
    """Blank out the arguments of test()/gsub()/match() and friends.

    Those are patterns being read, not taxonomy values being written. The
    arguments are found by matching parens rather than by a regex, because a
    jq regex routinely contains its own -- ``gsub("(?<c>[A-Z])"; "_" + (.c |
    ascii_downcase))`` would otherwise be cut short at the first ``)`` and
    leave ``"(?<c>[A-Z])"`` looking like an emitted literal.
    """
    text = expression or ""
    while True:
        found = READERS.search(text)
        if not found:
            return text
        depth, index = 0, found.end() - 1
        while index < len(text):
            if text[index] == "(":
                depth += 1
            elif text[index] == ")":
                depth -= 1
                if depth == 0:
                    break
            index += 1
        text = text[:found.start()] + " " + text[index + 1:]


def emitted_literals(expression):
    """String literals the expression can emit."""
    return re.findall(r'"([^"\\]*)"', strip_reader_calls(expression))


PATH = re.compile(
    r"(?:\$[A-Za-z_]\w*|(?<![\w)\]\"])\.)"
    r"(?:[A-Za-z_]\w*|\[[^\]]*\])(?:\.[A-Za-z_]\w*|\[[^\]]*\])*"
)


def outer_parens_match(text):
    """True if text[0] is the paren closed by text[-1]."""
    if not text.startswith("(") or not text.endswith(")"):
        return False
    depth = 0
    for index, char in enumerate(text):
        if char == "(":
            depth += 1
        elif char == ")":
            depth -= 1
            if depth == 0:
                return index == len(text) - 1
    return False


def split_alternatives(expression):
    """Split a jq ``a // b // c`` chain at depth 0, outermost parens removed."""
    text = " ".join((expression or "").split())
    while outer_parens_match(text):
        text = text[1:-1].strip()
    parts = []
    depth = 0
    in_string = False
    start = 0
    index = 0
    while index < len(text):
        char = text[index]
        if in_string:
            if char == "\\":
                index += 2
                continue
            if char == '"':
                in_string = False
        elif char == '"':
            in_string = True
        elif char in "{[(":
            depth += 1
        elif char in "}])":
            depth -= 1
        elif char == "/" and depth == 0 and text[index:index + 2] == "//":
            parts.append(text[start:index].strip())
            index += 2
            start = index
            continue
        index += 1
    parts.append(text[start:].strip())
    return [part for part in parts if part]


def split_top(text, operator):
    """Split ``text`` on a depth-0 occurrence of a single-character operator."""
    parts = []
    depth = 0
    in_string = False
    start = 0
    for index, char in enumerate(text):
        if in_string:
            if char == '"':
                in_string = False
        elif char == '"':
            in_string = True
        elif char in "{[(":
            depth += 1
        elif char in "}])":
            depth -= 1
        elif char == operator and depth == 0:
            parts.append(text[start:index])
            start = index + 1
    parts.append(text[start:])
    return [part.strip() for part in parts]


def concatenates_a_literal(expression):
    """True for a ``+`` concatenation with a string-literal operand.

    jq treats null as the identity for ``+``, so ``null + ":" + null`` is
    ``":"``, not null. Without this, every ``(.a + ":" + .b)`` name reads as a
    null risk.
    """
    text = " ".join((expression or "").split())
    while outer_parens_match(text):
        text = text[1:-1].strip()
    operands = split_top(text, "+")
    if len(operands) < 2:
        return False
    return any(re.fullmatch(r'"[^"]*"', operand) for operand in operands)


SAFE_FILTERS = ("ascii_downcase", "ascii_upcase", "tostring", "tojson",
                "tonumber", "length", "ltrimstr", "rtrimstr")


def balanced_prefix(text, close):
    """Inner text of the parenthesised group whose ``)`` is at index ``close``.

    Scans backwards, so it copes with the parens inside a jq regex literal such
    as ``capture("(?<t>[^/]+)")`` -- those are balanced, which is what matters.
    """
    depth = 0
    index = close
    while index >= 0:
        if text[index] == ")":
            depth += 1
        elif text[index] == "(":
            depth -= 1
            if depth == 0:
                return text[index + 1:close]
        index -= 1
    return None


def pipeline_is_safe(alternative, paths):
    """``X | ascii_downcase`` cannot be null when ``X`` is proven non-null."""
    stages = split_top(alternative, "|")
    if len(stages) < 2:
        return False
    head = stages[0]
    while outer_parens_match(head):
        head = head[1:-1].strip()
    if head not in paths:
        return False
    return all(
        any(stage.startswith(name) for name in SAFE_FILTERS)
        for stage in stages[1:]
    )


def proven_non_null(query):
    """What the query proves before it builds the record.

    Returns ``(paths, chains)``. ``paths`` are individually non-null. ``chains``
    are alternative sets proven non-null *collectively*: ``select((.a // .b //
    null) != null)`` does not prove either ``.a`` or ``.b`` on its own, but it
    does prove that ``.a // .b`` is never null.
    """
    source = strip_comments(query)
    paths = set()
    chains = []

    def record(candidate):
        alternatives = [
            alternative for alternative in split_alternatives(candidate)
            if alternative and alternative != "null"
        ]
        if len(alternatives) == 1:
            paths.add(alternatives[0])
        elif alternatives:
            chains.append(frozenset(alternatives))

    for match in re.finditer(r"select\s*\(([^()]*(?:\([^()]*\)[^()]*)*)\)", source):
        condition = match.group(1)
        for inner in re.finditer(
            r"(\([^()]*\)|\$?[\w.\[\]]+)\s*!=\s*null", condition
        ):
            record(inner.group(1))
        if re.search(r"(?:^|[\s(])\.\s*!=\s*null", condition):
            paths.add(".")
        # `select((.x | type) == "string")` -- null has type "null", so passing
        # this proves .x is not null.
        for inner in re.finditer(
            r"\(\s*(\$?[\w.\[\]]+)\s*\|\s*type\s*\)\s*==", condition
        ):
            paths.add(inner.group(1))
        # `select(.x | test("..."))` -- test() raises on null, so reaching the
        # record at all proves .x was a string.
        for inner in re.finditer(
            r"^\s*(\$?[\w.\[\]]+)\s*\|\s*(?:test|startswith|endswith)\b",
            condition,
        ):
            paths.add(inner.group(1))
    # `if (.a // null) != null and (.b // null) != null then ...`
    for match in re.finditer(r"(\([^()]*\))\s*!=\s*null", source):
        record(match.group(1))

    # Variable bindings. `(.kind // "missing") as $kind` cannot be null, and
    # neither can `($data.id | ascii_downcase) as $arm_id` once `$data.id` is
    # proven. A binding can depend on an earlier binding, so iterate to a fixed
    # point rather than making a single pass.
    bindings = []
    for match in re.finditer(r"\)\s+as\s+(\$[A-Za-z_]\w*)", source):
        inner = balanced_prefix(source, match.start())
        if inner is not None:
            bindings.append((inner.strip(), match.group(1)))
    for match in re.finditer(
        r"(?<![)\w])(\$?[\w.\[\]]+)\s+as\s+(\$[A-Za-z_]\w*)", source
    ):
        bindings.append((match.group(1), match.group(2)))

    while True:
        before = len(paths)
        for expression, variable in bindings:
            if variable not in paths and not can_be_null(expression, (paths, chains)):
                paths.add(variable)
        if len(paths) == before:
            return paths, chains


def can_be_null(expression, proven):
    """True if this value expression can evaluate to null.

    jq's ``//`` yields the first alternative that is neither null nor false, so
    a chain is non-null as soon as *any one* of its alternatives is non-null.
    Treating the whole expression as a single reference -- which is what a naive
    check does -- reports a false positive on every guarded fallback chain.
    """
    if expression is None:
        return True
    paths, chains = proven
    alternatives = split_alternatives(expression)

    for alternative in alternatives:
        if alternative == "null":
            continue
        if re.fullmatch(r'"[^"]*"|\{\}|\[\]|-?\d+|true|false', alternative):
            return False            # a non-null literal ends the chain
        if concatenates_a_literal(alternative):
            return False            # null is the identity for jq's `+`
        if alternative in paths:
            return False            # proven non-null by an earlier guard
        if "tostring" in alternative or "tojson" in alternative:
            return False            # coerced to a string
        if pipeline_is_safe(alternative, paths):
            return False            # `<proven> | ascii_downcase` and friends
        if not PATH.findall(alternative):
            return False            # no path reference, cannot be null

    if any(chain <= set(alternatives) for chain in chains):
        return False                # a guard proved this exact chain non-null

    return True


# --------------------------------------------------------------------------
# Tests
# --------------------------------------------------------------------------

def test_query_file_exists_and_parses():
    assert os.path.isfile(QUERY_FILE), "%s is missing" % QUERY_FILE
    assert QUERIES, "%s declares no queries" % QUERY_FILE


@pytest.mark.parametrize("module", MODULES)
def test_module_key_is_fully_qualified(module):
    parts = module.split(".")
    assert len(parts) == 3, (
        "'%s' is not of the form namespace.collection.module. host_indirect.py "
        "skips any key that does not split into exactly three parts, so this "
        "query would never run." % module
    )


@pytest.mark.parametrize("module", MODULES)
def test_emits_a_name_that_cannot_be_null(module):
    record = emitted_record(QUERIES[module])
    assert record is not None, "%s: could not find the emitted record object" % module
    pairs = dict(split_pairs(record))

    assert "name" in pairs, (
        "%s emits no top-level `name`. host_indirect.py does `if name is None: "
        "continue`, so every node this module reports is discarded." % module
    )
    assert not can_be_null(pairs["name"], proven_non_null(QUERIES[module])), (
        "%s: `name` can evaluate to null (%s). Give it a non-null fallback or "
        "guard the record with select()." % (module, pairs["name"])
    )


@pytest.mark.parametrize("module", MODULES)
def test_canonical_facts_is_present_and_non_empty(module):
    pairs = dict(split_pairs(emitted_record(QUERIES[module])))
    assert "canonical_facts" in pairs, (
        "%s emits no `canonical_facts`. host_indirect.py does "
        "`if not data.get('canonical_facts'): continue`." % module
    )
    assert sub_object(pairs["canonical_facts"]), (
        "%s emits an empty `canonical_facts`. An empty dict is falsy, so the "
        "record is discarded." % module
    )


@pytest.mark.parametrize("module", MODULES)
def test_no_field_in_canonical_facts_can_be_null(module):
    """The defect class that has no name in any documentation.

    ``get_hashable_form()`` raises ``UnhashableFacts`` on ``None``. The caller
    catches it and skips the record -- silently, logged once per job at INFO,
    with the job still green. A single optional field referenced without a
    fallback discards the entire node.

    Note that ``// null`` does not make a field optional. It guarantees the
    drop. If a field may be absent, either omit the key or move it to ``facts``.
    """
    query = QUERIES[module]
    pairs = dict(split_pairs(emitted_record(query)))
    proven = proven_non_null(query)
    nullable = [
        "canonical_facts.%s = %s" % (key, value)
        for key, value in sub_object(pairs.get("canonical_facts", "")).items()
        if can_be_null(value, proven)
    ]
    assert not nullable, (
        "%s: these canonical_facts fields can evaluate to null, which discards "
        "the whole record:\n    %s\nGuard the source with select(... != null), "
        "give a non-null fallback, or move the field to `facts` (not hashed)."
        % (module, "\n    ".join(nullable))
    )


@pytest.mark.parametrize("module", MODULES)
def test_canonical_facts_holds_identity_only(module):
    """canonical_facts is the sole dedup key, so anything mutable in it overcounts."""
    pairs = dict(split_pairs(emitted_record(QUERIES[module])))
    fields = sub_object(pairs.get("canonical_facts", ""))
    lowered = set(key.lower() for key in fields)

    volatile = sorted(lowered & VOLATILE_KEYS)
    assert not volatile, (
        "%s: canonical_facts contains mutable field(s) %s. canonical_facts is "
        "the only dedup key (results[hashable_facts]), so the same node is "
        "counted again every time one of these changes. Move them to `facts`, "
        "which is not hashed." % (module, ", ".join(volatile))
    )

    identifiers = sorted(lowered & IDENTITY_KEYS)
    labels = sorted(lowered & DISPLAY_NAME_KEYS)
    assert not (labels and identifiers), (
        "%s: canonical_facts contains both the label(s) %s and the stable "
        "identifier(s) %s. A label is mutable, so renaming the object counts it "
        "as a second node. Keep the identifier, move the label to `facts`."
        % (module, ", ".join(labels), ", ".join(identifiers))
    )

    module_name = module.split(".")[-1]
    discriminators = sorted(
        key for key, value in fields.items()
        if re.fullmatch(r'"%s"' % re.escape(module_name), (value or "").strip())
    )
    assert not discriminators, (
        "%s: canonical_facts.%s is the module's own name. One physical node "
        "touched by two modules in this collection then produces two audit "
        "rows. Move it to `facts`."
        % (module, ", ".join(discriminators))
    )


@pytest.mark.parametrize("module", MODULES)
def test_facts_carry_the_full_taxonomy(module):
    pairs = dict(split_pairs(emitted_record(QUERIES[module])))
    assert "facts" in pairs, (
        "%s emits no `facts`. The node is counted but cannot be bucketed, so it "
        "is invisible in every rollup." % module
    )
    facts = sub_object(pairs["facts"])
    missing = [key for key in TAXONOMY_KEYS if key not in facts]
    assert not missing, "%s: facts is missing %s" % (module, ", ".join(missing))


@pytest.mark.parametrize("module", MODULES)
def test_taxonomy_values_are_normalized(module):
    """Assert the shape, not the value.

    An equality assertion against a captured literal cannot catch a value that
    only appears for a resource type nobody wrote a fixture for -- which is
    exactly where ``mapping[$x] // $x`` fallbacks leak raw API strings.
    """
    facts = sub_object(dict(split_pairs(emitted_record(QUERIES[module]))).get("facts", ""))
    bad = [
        "facts.%s = %r" % (key, literal)
        for key in TAXONOMY_KEYS
        for literal in emitted_literals(facts.get(key))
        if literal and not NORMALIZED.match(literal)
    ]
    assert not bad, (
        "%s: taxonomy values must match %s (lowercase_with_underscores). "
        "Unnormalised values become separate buckets downstream:\n    %s"
        % (module, NORMALIZED.pattern, "\n    ".join(bad))
    )
