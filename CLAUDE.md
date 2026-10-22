# CLAUDE.md — Payment Reconciliation Exceptions Agent

## Who I am and why this project exists
- I'm a senior Java backend developer (~12 years in banking/fintech: Spring Boot, Apache Camel, integrations, payments, CRM).
- I'm learning Python and building AI agents. This project is (1) my learning vehicle and (2) a portfolio piece for "AI Agent Engineer" roles.
- Interviewers will ask me *why* every design decision was made. I must understand and be able to defend all code in this repo. Optimize for my understanding, not just for working code.
- I know the banking domain well. Python and agent concepts are new — explain those; don't over-explain banking basics.

## What we are building
An agent that handles **reconciliation exceptions**: transactions from a bank statement that did not auto-match with the internal ledger.

Pipeline:
ingest statement + ledger → normalize → **deterministic matching** (exact amount/date/reference) → for unmatched items the agent investigates: finds the likely counterpart(s) and the reason (bank fee, partial payment, reference typo, FX difference, duplicate, reversal, split payment, genuinely missing entry) → proposes an adjustment with reasoning → **human approval by an operator** → posts the adjustment (idempotent).

Principle: **deterministic code does what it can, the LLM handles only the fuzzy remainder.** The LLM never decides money movement on its own.

## Data
- All data is **synthetic**, produced by our own generator with a fixed seed. No real customer data, ever.
- The generator injects known exception types and writes a ground-truth labels file — this is the basis for evals.
- Statement formats: CSV and ISO 20022 camt.053 (XML). Ledger: CSV / Postgres table.

## Stack
- Python 3.12, `uv` for dependencies, `ruff` + `mypy` (strict-ish), `pytest`
- LangGraph (state graph, Postgres checkpointer, interrupts for human-in-the-loop)
- MCP servers via the official MCP Python SDK (FastMCP)
- LiteLLM as the LLM gateway (model tiering, budgets, fallbacks); AWS Bedrock as provider (Anthropic API allowed for local dev)
- Postgres (ledger, checkpoints, memory), Langfuse / OpenTelemetry for tracing
- Docker Compose for local env, GitHub Actions for CI, AWS for deployment (later)

## Repository layout
```
data/
  generator/          # synthetic statement + ledger generator with injected exceptions
  samples/            # small committed sample datasets + labels.json (ground truth)
src/recon/
  models.py           # StatementTx, LedgerEntry, Exception case, Adjustment (pydantic)
  parsers/            # csv_statement.py, camt053.py, ledger.py
  matching/           # deterministic matcher (exact rules), outputs matched + unmatched
  mcp_servers/
    statements/       # read-only: list_unmatched, get_statement_tx, search_statement
    ledger/           # read-only: search_ledger, get_entry, get_account_history
    reference/        # read-only: counterparty directory, fee schedules, FX rates, past cases
    postings/         # WRITE: post_adjustment (idempotent, approval-gated)
  agent/              # LangGraph graph, nodes, state, prompts
  memory/             # per-account store of operator decisions on past cases
  gateway/            # LiteLLM config
evals/                # eval runners and metrics against labels.json
tests/                # unit + integration + failure-injection tests
docs/learning/        # learning notes per module (Russian)
DECISIONS.md          # architecture decision log
README.md             # portfolio-facing overview (English)
```

## Hard rules (never break these)
- **Money is `Decimal`, never `float`.** Amounts carry currency. (Java analogy: `BigDecimal` + currency, never `double`.)
- Any action with side effects (posting adjustments, writing to the ledger) must go through an explicit **human approval** step in the graph. The agent only proposes.
- Write-tools are **idempotent**: idempotency key derived from case id + proposed adjustment content. Re-calling must not double-post.
- Every proposed and posted adjustment keeps an **audit trail**: inputs, tool calls, model reasoning summary, approver, timestamp.
- Memory and data are isolated per account/client. No cross-account reads.
- No secrets in code or commits. `.env` (gitignored) locally, AWS Secrets Manager in the cloud. Provide `.env.example`.
- Synthetic data only.

## How to work with me
1. **Plan first.** Before writing code for a new module, give me a short plan: components, key decisions, 1–2 alternatives you rejected and why. Wait for my OK.
2. **Small steps.** One module or one meaningful change per step. After each step: run `ruff`, `mypy`, `pytest`, and summarize what changed.
3. **Don't over-engineer.** No abstractions, layers or dependencies I didn't ask for. If you think something is needed, propose it, don't add it.
4. **Ask when unsure** about a design decision instead of guessing.
5. **Make failures visible.** No silent `except: pass`. Errors are logged with context and either handled explicitly or re-raised.

## Code comments
- Comment the **why**, not the what. Explain non-obvious decisions, edge cases, failure modes.
- When a Python or agent concept differs from Java, a short Java analogy is welcome, e.g. `# like @Transactional, but ...` or `# pydantic model ≈ Java record + Bean Validation`.
- Keep comments production-quality: this repo will be reviewed by hiring managers. No tutorial-style essays in code — those go to `docs/learning/`.
- Code, comments, README, DECISIONS.md — in **English**.

## Learning notes (docs/learning/)
After finishing each module, create or update `docs/learning/<NN>-<module>.md` **in Russian** with:
1. **Что делает модуль** и как он вписывается в систему (1 абзац + место в пайплайне)
2. **Ключевые концепции** простым языком (tool use loop, MCP, чекпоинты LangGraph, evals и т.п.). Где уместно — сравнение с Java/Spring/Camel.
3. **Python-особенности**, которые встретились в этом модуле (async, type hints, pydantic, Decimal, context managers, генераторы и т.п.)
4. **Альтернативы**: что ещё можно было сделать и почему выбрано это
5. **Что может сломаться** и как это проявится (симптомы в логах/трейсах)
6. **Вопросы для самопроверки**: 3–5 вопросов в стиле технического интервью (без ответов)
7. **Упражнение**: одно небольшое изменение, которое я должен сделать сам руками

## Decision log (DECISIONS.md)
For every architectural decision, append an entry:
```
## ADR-NNN: <title>
- Context:
- Options considered:
- Decision:
- Consequences / trade-offs:
```

## Testing expectations
- Unit tests for parsers, matcher and pure logic (amount/currency handling especially).
- Integration tests for MCP servers and graph nodes (mock the LLM where behavior is deterministic).
- Failure-injection tests: tool timeout, malformed file, process crash mid-run (resume from checkpoint), duplicate approval / repeated post_adjustment.
- Evals (separate from tests): run against `labels.json`, measure exception-type accuracy, correct counterpart match rate, false "auto-fix" proposals; later gated in CI.

## Commands
- Install: `uv sync`
- Lint/types: `uv run ruff check . && uv run mypy src`
- Tests: `uv run pytest`
- Generate data: `uv run python -m data.generator --seed 42 --out data/samples/`
- Local infra: `docker compose up -d`
