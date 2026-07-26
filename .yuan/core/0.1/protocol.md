# Yuan Core Protocol 0.1

> Revision: `yuan.core.protocol/0.1.0-candidate`
>
> Status: inert candidate. This document and its sibling schemas do not become
> runtime authority until an older trust root independently accepts them.

## 1. Boundary

Yuan Core is a deterministic engineering harness around a nondeterministic LLM.
The LLM may propose; it is never the source of facts, tool authority, evidence
validity, or completion.

Core has exactly five primitives:

1. **Protocol** — the rules in this document.
2. **Work Contract** — immutable intent, typed acceptance criteria, constraints,
   authorization, budgets, and verifier bindings.
3. **Run Memory** — a bounded, disposable projection of current state.
4. **Attempt** — one bounded strategy and its side-effect journal.
5. **Evidence** — immutable external observations bound to what was checked.

Knowledge, roles, agents, phases, Git, reviews, deployment, TDD ordering, and
platform-specific schedulers are not Core. They may supply proposals or
Evidence, but cannot redefine this protocol.

## 2. Immutable bindings

`Protocol`, `Work Contract`, Harness, and every verifier are content-addressed
immutable revisions. Changing content creates a new revision and hash. A Work
revision pre-binds every required typed AC to:

- verifier id, revision, SHA-256, and trust-root id;
- permitted environment ids;
- artifact scope;
- a positive minimum assertion count.

The LLM cannot replace a verifier after observing a result. A revision/hash
mismatch is invalid input, never an implicit upgrade.

## 3. Tick

One Tick performs this finite sequence:

1. Read bound Protocol and Work revisions plus Run Memory.
2. Rebuild Run Memory first if its bindings or source digests are invalid.
3. Load only the artifact and Evidence pointers needed for the current decision.
4. Accept at most one LLM hypothesis and at most one mutating action proposal.
5. Validate scope, authorization, budgets, relevant-input fingerprint, strategy
   repetition, and verifier binding.
6. Before any side effect, durably append `PREPARED`; then journal execution.
7. Execute only through a bound Port and record its structured tool receipt.
8. Run the pre-bound verifier and validate its Evidence fail-closed.
9. Deterministically reduce to exactly one Tick result.
10. Atomically replace the Run Memory projection using compare-and-swap.

No-new-evidence repetition is rejected:

```text
same strategy_fingerprint
+ same relevant input hashes
+ no newer relevant Evidence
= no execution
```

## 4. Side-effect journal

A non-mutating Attempt uses `NOT_APPLICABLE`. A mutating Attempt follows only:

```text
PREPARED → EXECUTING → OBSERVED → COMMITTED
                         └──────→ UNKNOWN
             └─────────────────→ UNKNOWN
```

- `PREPARED` must be durable before the tool is invoked.
- `EXECUTING` means the tool may have changed the world.
- `OBSERVED` requires a structured receipt but is not yet committed truth.
- `COMMITTED` requires the postcondition and receipt to be durably bound.
- Any crash, cancellation, timeout, lost receipt, ambiguous postcondition, or
  illegal journal transition after execution begins becomes `UNKNOWN`.

`UNKNOWN` is fail-closed: it blocks completion and automatic re-execution. Only
an independent reconciliation Attempt may establish what happened. The LLM
must not call side-effecting tools outside the Harness/Port route.

## 5. Evidence validity

Evidence is append-only and valid only when all applicable checks hold:

1. schema and semantic validation succeed;
2. status is `PASS`;
3. assertion count is positive and equals the number of uniquely identified
   checks; every check passes;
4. artifact scope and SHA-256 equal the current artifact;
5. environment id and fingerprint equal the declared execution environment;
6. verifier id, immutable revision, SHA-256, and trust-root id equal the Work
   AC's pre-binding;
7. harness revision/hash and source Attempt are present;
8. stdout, stderr, and receipt digests are present;
9. independence is explicit and valid for the AC;
10. freshness window, when declared, has not expired.

Verifier crash, timeout, cancellation, zero assertions, missing or unparsable
logs, stale artifact, wrong scope/environment, unbound verifier, duplicate
check ids, and self-attestation all yield invalid Evidence. An exit code of zero
or review statement alone never supplies validity.

## 6. Completion predicate

```text
COMPLETE :=
  every required typed AC has valid, independent Evidence
  AND every Evidence item targets the current artifact and environment
  AND every declared safety invariant is true
  AND every side effect is COMMITTED or NOT_APPLICABLE
  AND no side effect is pending or UNKNOWN
```

Task terminality, LLM assertion, exit code zero, zero tests, review approval,
clean Git state, documentation, commit, merge, deployment, or Run Memory's
stored result cannot independently imply completion.

## 7. Exactly six results and frozen priority

The reducer evaluates the following ordered rules and returns on the first
match. This priority makes the results mutually exclusive:

1. `BLOCKED` — state is inconsistent; a side effect is `UNKNOWN`; or no safe
   legal next step exists.
2. `WAIT_AUTH` — a concrete otherwise-legal next step exceeds a Work grant.
3. `BUDGET_EXIT` — any bound Tick, tool, strategy, or command-time budget is
   exhausted. This is never success.
4. `COMPLETE` — and only when the completion predicate in §6 is true.
5. `CORRECT` — new Evidence refutes the active hypothesis and a different
   strategy remains legal and within budget.
6. `CONTINUE` — new Evidence advances an unmet AC and a legal next step exists.

If none matches, return `BLOCKED`. Result names are exactly:

```text
CONTINUE CORRECT COMPLETE BLOCKED WAIT_AUTH BUDGET_EXIT
```

## 8. Scope, authorization, and budget

Every action declares its type, mutability, relative scope, and budget charge.
The Harness rejects absolute or escaping filesystem paths, symlink/junction
escape, shell command strings, unbound executables, undeclared side-effect
classes, and charges beyond remaining budget.

Authorization is deny-by-default. A grant matches action type, side-effect
class, and scope. Expired, absent, ambiguous, or broader-than-Work grants do not
authorize execution. Human confirmation is required only for an otherwise legal
step outside the frozen grant, a high-impact side effect, or a value judgment.

Budgets are immutable maxima in Work and decrement in Run Memory. Exhaustion
produces `BUDGET_EXIT`; silently extending a budget creates a new Work revision.

## 9. Run Memory rebuild

Run Memory is not history and not authority over its sources. It stores bounded
pointers and digests for:

- the bound Work and Protocol revisions;
- current artifact/environment;
- remaining budgets;
- required AC → Evidence ids;
- at most three active hypotheses and three legal next steps;
- non-terminal/UNKNOWN side effects;
- Attempt and Evidence source ids plus their aggregate digests.

If missing, corrupt, stale, or inconsistent, discard it and deterministically
replay the immutable Work, ordered Attempts, and Evidence. Missing history,
digest mismatch, invalid transitions, or ambiguous ordering is `BLOCKED`; it
must never reconstruct `COMPLETE`.

## 10. Minimal Port

The platform boundary exposes only:

- scoped file read and atomic compare-and-swap write with hashes;
- bounded, cancellable command execution without a shell and with a structured
  receipt;
- one LLM proposal call through an explicitly bound provider interface.

An unavailable capability is `UNSUPPORTED`, not a semantic fallback. Tool
receipts include operation id, status, timing, scope/argv, exit state, output
digests, truncation flags, and before/after hashes where applicable.

## 11. Self-modification

A candidate must not establish its own trust. Core, Harness, schema, validator,
or authority changes require acceptance by at least one of:

1. the previous immutable trust root;
2. an independent held-out verifier rooted outside the candidate;
3. explicit human authorization that names the revision and risk.

Candidate conformance and author tests are development evidence only. Validator
failure, empty validation, or missing independent root blocks authority switch.

## 12. Inert-candidate rule

Files in this directory define a candidate only. They must not modify the
repository entrypoint, current runtime authority, initializer, pre-commit
configuration, or existing user work. Authority changes require later migration
milestones and independent Evidence.
