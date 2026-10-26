# tox-ansible matrix action

This composite action runs `tox --ansible --gh-matrix`, filters the generated
environments to unit and sanity tests, then appends missing environments from a
collection-specific JSON file. The resulting JSON is exposed as the `envlist`
output for a GitHub Actions matrix. Companion entries bridge combinations that
tox-ansible does not generate yet; upstreaming support for those combinations is
a follow-up.

The caller must check out the collection before using the action. Its matrix
configuration is a path relative to the caller's workspace and has this shape:

```json
{
  "companion_envs": [
    {"name": "unit-constraints", "python": "3.11"}
  ]
}
```

Use it in the current repository with:

```yaml
- id: matrix
  uses: ./.github/actions/tox-ansible-matrix
  with:
    matrix-config: .github/tox-ansible-matrix.json
```

Other collections can reuse the action from this repository and pass their own
matrix configuration. The action-specific tool pins are in `requirements.txt`.
Collection-wide constraints and compiled test dependency lockfiles are part of
the separate dependency-consolidation work, not this CI workflow change.
