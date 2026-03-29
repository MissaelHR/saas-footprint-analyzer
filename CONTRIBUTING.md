# Contributing

## Setup

```bash
python3.12 -m venv .venv
source .venv/bin/activate
pip install -e .[dev]
```

## Standards

- Run `make lint` and `make test` before opening a change.
- Keep Datadog-specific logic inside `src/saas_footprint_analyzer/datadog`.
- Keep CLI handlers thin. Domain logic belongs in library modules.
- Add tests for new behavior and regressions.

## Pull requests

PRs should include:

- A clear problem statement
- The reasoning behind the chosen approach
- Tests covering the change
- Documentation updates when user-facing behavior changes
