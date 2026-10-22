# Architecture Decision Log

## ADR-001: Tooling and project layout
- Context: New Python 3.12 project that must be reproducible locally and in CI, reviewed by others, and grow into several modules (parsers, matcher, MCP servers, agent).
- Options considered:
  - Dependency management: pip + requirements.txt; Poetry; uv.
  - Layout: flat (`recon/` at repo root); src layout (`src/recon/`).
  - Type checking: none; mypy default; mypy strict.
- Decision: uv (with committed `uv.lock` and `.python-version`), src layout built with `uv_build`, ruff for lint + format, mypy in `strict` mode, pytest. Dev tools live in the `dev` dependency group.
- Consequences / trade-offs:
  - uv gives one tool for Python version, venv, resolution and lock file; CI runs `uv sync --locked` so drift between `pyproject.toml` and the lock fails the build. Less mature ecosystem than pip/Poetry.
  - src layout forces tests to import the installed package, catching packaging errors early; costs one extra directory level.
  - Strict mypy catches `None`/type errors early (important for money-handling code); untyped third-party libs need per-module overrides instead of global relaxation.
