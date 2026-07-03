# Contributing to auto-fio

`main` is always meant to be installable and green across macOS, Windows, and
Linux. All changes land via a pull request from a short-lived feature branch —
never commit or push directly to `main`.

## Workflow

- One branch per unit of work, named after the work (`feat/…`, `fix/…`,
  `test/…`, `docs/…`); tests ship in the same branch as the code they cover.
- Open a PR into `main`, let CI go green, then merge and delete the branch.
- Milestones are annotated tags, not branches.

## Run the checks locally

```bash
pip install ".[dev]"
ruff check src tests
pytest
```

## Enable the local guardrail hook (once per clone)

```bash
git config core.hooksPath .githooks
```

## Commit messages

Write clear, self-authored messages. Do **not** add `Co-Authored-By` /
AI-attribution trailers.
