# task-010 M7 Extensions and Clause Provenance

> Role: Doc Engineer
> Source HEAD: `c506b919e7a8af8dd1b0c8f3a230b16573cba7cc`
> Verdict: `PASS — M7 author/G4 gate`

## Boundary

- Added six optional Extensions: software delivery, testing, DocsOS, Knowledge,
  UI, and platform Adapters.
- Every Extension consumes only the public Core Protocol/record schemas and may
  produce only Work authoring advice or immutable Evidence.
- No Extension adds a primitive or Tick result, changes `COMPLETE`, writes
  runtime authority, or becomes a Core prerequisite.
- No Core file, legacy normative source, Adapter descriptor, authority pointer,
  or protected user dirty file was modified.
- Legacy carriers remain in place. M7 does not authorize tombstoning.

## Extracted valid knowledge

The Extension layer retains:

- externalized bounded state and “Protocol over Platform”;
- bounded convergence and no same-strategy/no-new-Evidence retry;
- actor/checker separation, held-out validation, integrity diff, and
  anti-gaming;
- real/isolated environment contract verification rather than mock-only proof;
- `PIT-003` template/runtime separation and `PIT-004` content preservation;
- separate `merged`, `deployed`, and `live verified` claims;
- `.yuan/VERSION` as the single framework-version source;
- ten content-bound negative fixtures selected from legacy failures.

These are optional authoring/verifier practices. None is promoted into Core
runtime semantics.

## Reproducible provenance

Commands:

```text
python -B scripts/yuan-provenance.py generate
python -B scripts/yuan-provenance.py verify
```

Result:

| Metric | Value |
|--------|------:|
| Source files | 177 |
| Source bytes | 1,435,630 |
| Clauses | 1,701 |
| Mapped | 1,701 |
| Unmapped | 0 |
| Coverage | 100.00% |

Disposition:

| Category | Clauses |
|----------|--------:|
| Core | 47 |
| Extension | 1,046 |
| Knowledge | 588 |
| Fixture | 19 |
| Obsolete-with-proof | 1 |

The one obsolete full-file clause is the untrusted
`scripts/run-ptg-cal-check.py`. Its record binds the source hash, failure
reason, Core replacement, and negative fixture. Every Markdown source is
partitioned by ATX heading outside fenced code; preamble and unheaded/non-
Markdown files receive complete content hashes.

Required scope families are present:

```text
AGENTS / README / contracts / .yuan core+specs+rules+docs+skills+platforms
/ protocols / templates / docs policies / references / scripts / VERSION
/ initializer
```

Archive, runtime Workspace state, event/evidence journals, shadow/run
projections, repository tests, caches, and generated Extension outputs are
excluded with machine-readable reasons. The current Genesis and M3–M6 evidence
remain Gate inputs, not legacy clauses.

## Regression and integrity

```text
provenance verify:          1,701/1,701 mapped, links/hash PASS
M1 bootstrap:              31/31 PASS
Core author:               35/35 PASS
M3 independent held-out:   30/30 PASS
M4 shadow migration:       10/10 PASS
M5 canary:                  1/1 PASS (13 internal checks)
M6 adapter conformance:     8/8 PASS
old Genesis trust root:     80 checks / 7 cases PASS
M0a protected dirty:        10/10 hashes PASS
```

Machine-readable details and artifact hashes are in
[`final-verification.json`](final-verification.json).
