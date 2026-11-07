# Contributing to CampusRoute AI

Contributions are welcome. Please keep changes focused, explainable and
testable.

## Development setup

```bash
python -m venv .venv
python -m pip install -r requirements-dev.txt
python -m pytest -q
python -m ruff check .
```

## Workflow

1. Create a focused branch such as `fix/map-validation`.
2. Make the smallest change that solves the issue.
3. Add a regression test for new behaviour.
4. Run pytest and Ruff locally.
5. Update documentation when public behaviour changes.
6. Open a pull request explaining the problem, design and tests.

## Pull request checklist

- [ ] Tests pass.
- [ ] Ruff passes.
- [ ] No secrets or private GPS data are included.
- [ ] Map changes include validation tests.
- [ ] API compatibility was considered.
- [ ] Documentation is updated.

Do not present synthetic maps, ETA estimates or browser GPS as production
guarantees.
