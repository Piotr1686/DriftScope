# Contributing to DriftScope

DriftScope is a single-author research / portfolio project, but issues, questions, and
well-scoped pull requests are welcome. This guide describes the local setup and the quality
bar the project holds itself to.

## Development setup

Requires **Python 3.10**.

```bash
pip install -e ".[dev]"
# Windows 11 / Miniconda SSL workaround, if needed:
#   --trusted-host pypi.org --trusted-host files.pythonhosted.org
```

A quick environment sanity check:

```bash
python scripts/smoke_test.py
```

## Quality gates (must pass before a PR)

The same three checks run in CI (`.github/workflows/ci.yml`, Ubuntu / Python 3.10):

```bash
ruff check src tests          # lint + import order
mypy --strict src             # strict typing
pytest -q                     # full suite
```

## Conventions

- **Commits:** Conventional Commits — `feat:`, `fix:`, `docs:`, `refactor:`, `chore:`, `style:`.
- **Code comments** are written in Polish (project convention); identifiers and public docs are English.
- **Data handling:** Polars, not pandas. CPU-only by design — no GPU / JAX.
- **Style & typing:** ruff for everything; `mypy --strict` is the priority gate for `methodology/`.

## The pre-registration discipline (important)

Any change under `src/driftscope/methodology/` that alters a **statistical decision** — a
statistic, null model, threshold, or effect-size grid — must be accompanied by an update to
`methodology/preregistration_v*.md` carrying a `revision_reason`, explicitly split into
*clean* (a specification fix decided before seeing results) vs *data-informed*. This §0
discipline underpins the project's honesty claims. Pure typing / refactor / reporting changes
do **not** require a pre-registration revision.

## Reporting a bug or proposing an idea

Please use the issue templates. For anything touching the methodology, describe the
pre-registration implication so it can be discussed before code is written.

## License

By contributing you agree that your contributions are licensed under the project's
[MIT License](LICENSE).
