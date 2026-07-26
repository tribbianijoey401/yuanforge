# Clause Provenance

M7 maps every clause in the declared normative scope to exactly one disposition:

```text
core | extension | knowledge | fixture | obsolete-with-proof
```

## Reproduce

From the repository root:

```text
python -B scripts/yuan-provenance.py generate
python -B scripts/yuan-provenance.py verify
```

`generate` derives [`scope-manifest.json`](scope-manifest.json),
[`clause-manifest.json`](clause-manifest.json), and
[`REPORT.md`](REPORT.md) from [`scope-policy.json`](scope-policy.json) and the
current source bytes. `verify` regenerates in memory, requires byte equality,
checks 100% clause mapping, validates obsolete proof fields and source hashes,
checks fixture bindings and local Extension links, and rejects scope family
omissions.

Markdown is partitioned at ATX headings outside fenced code blocks. Bytes before
the first heading form `@preamble`; a file with no heading is one `@file`
clause. Non-Markdown files are always one full-file clause. Every record binds
the source-file SHA-256 and the exact clause SHA-256 with line boundaries.

## Scope boundary

The scope includes all framework entrypoints, contracts, legacy specs/rules/doc
templates/skills/platforms, protocols, templates, policies, references, Core
candidate, Adapter descriptors, version/init surfaces, and scripts. The exact
roots and required families are machine-readable in the policy.

The following are intentionally excluded:

- archived workspaces: immutable historical evidence, not active normative
  authority;
- active Workspace state, events, evidence, `PROGRESS`, decisions, and backlog:
  runtime state governed by `PIT-003`, not reusable framework clauses;
- `.yuan-shadow` and `.yuan-run`: runtime projections;
- repository `tests/`: executable validation evidence rather than legacy
  normative prose (Core candidate tests remain included with Core);
- `.git`, caches, and generated M7 Extension outputs.

Exclusion does not delete, weaken, or de-authorize those artifacts. Genesis
Design and M3–M6 evidence remain migration Gate inputs outside this legacy
clause inventory.
