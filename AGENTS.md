# Yuan Core bootstrap

This file is the platform-independent bootstrap for Yuan. It is intentionally
small. Long-lived policy belongs in Core protocol or an explicitly installed
Extension, not in this entrypoint.

## 1. Fail-closed activation

Before handling a project request:

1. Run `python -B scripts/yuan-authority.py verify`.
2. Resolve `.yuan/authority/current`, then its content-addressed record.
3. If either check is missing, invalid, stale, or ambiguous, return `BLOCKED`.
4. Obey exactly one active authority:
   - `core` → `.yuan-run` is writable runtime state; legacy `docs/` is read-only.
   - `legacy` → `docs/` is writable runtime state; `.yuan-run` is read-only.
5. Never dual-write or infer authority from directory presence.

All writes must pass the active-lane writer guard and required CAS. Existing
Work, Attempt, and Evidence objects in `.yuan-run` are immutable. Run Memory is
replaceable only with compare-and-swap and must remain rebuildable from those
immutable objects.

## 2. Runtime contract

LLM inference is one bounded Tick; there is no required daemon or platform
scheduler. Read `.yuan/core/0.1/protocol.md` and the referenced schemas before
advancing Work.

Core has five primitives:

- Protocol
- Work Contract
- Run Memory
- Attempt
- Evidence

Every Tick reduces to exactly one result:

- `CONTINUE`
- `CORRECT`
- `COMPLETE`
- `BLOCKED`
- `WAIT_AUTH`
- `BUDGET_EXIT`

`COMPLETE` is derived only from typed acceptance criteria, valid scoped
Evidence, preserved safety invariants, and no unresolved side effects.
Verifier failure, missing evidence, unknown effects, or unparseable state is
blocking—not success.

## 3. Harness boundary

Core defines semantics. Adapters map portable capabilities. Extensions may
advise authoring or produce Evidence, but cannot change Core truth or become a
hidden prerequisite. Human authorization is required only at a declared effect
boundary; all authorized effects require a journal.

Framework self-modification is ordinary Work and must use the same contract,
Evidence, authority, and verification path.

The distributed framework version comes only from `.yuan/VERSION`. Installation
copies bootstrap + Core + adapters, and only explicitly selected Extensions.

## 4. Legacy recovery

The exact pre-switch bootstrap and every preserved semantic clause remain
recoverable through `.yuan/authority/legacy-bindings/AGENTS.json`, bound to the
M0 SHA-256 and the independently approved M7 semantic registry. Do not edit or
delete legacy rules/contracts during the migration recovery window.
