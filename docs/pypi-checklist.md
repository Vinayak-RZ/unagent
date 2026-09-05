# PyPI publish checklist (human-gated)

Do **not** publish until a maintainer explicitly says to publish.

## Pre-publish

- [ ] `scripts/validate.sh` exits 0 on a clean checkout
- [ ] CI green on the release commit (test + extras + ui + package jobs)
- [ ] Version bumped in `pyproject.toml` and `CHANGELOG.md`
- [ ] `python -m build` produces sdist + wheel; install wheel in a fresh venv
- [ ] `python -m superdeterminism --help` and `unagent-mcp --help` work from the wheel
- [ ] README quickstart works offline with fixtures (no live sink keys)
- [ ] Security review notes reviewed (`docs/security-review-phase-h.md`)
- [ ] Tag annotated: `git tag -a vX.Y.Z -m "Unagent vX.Y.Z"`

## Publish (maintainer only)

```bash
python -m build
python -m twine check dist/*
python -m twine upload dist/*   # only after explicit approval
```

## Post-publish

- [ ] GitHub Release notes link CHANGELOG + Studio GIF (user-owned)
- [ ] Confirm install: `pip install superdeterminism==X.Y.Z`
- [ ] No secrets in uploaded artifacts
