# Quality Audit: task-010 / commit 8513dae

> Reviewer: independent Quality Auditor
> Reviewed revision: `8513dae` (`docs(task-010): extract extensions and provenance`)
> Timestamp: 2026-07-27 01:33 +08:00
> Gate: M7 provenance / Extension boundary
> Result: **FAIL — return task-010-r1; task-011 must not consume M7**

```yaml
verdict: fail
blocking:
  - violation: "M7-B01: 100% provenance is manufactured by a default catch-all, not clause-level semantic disposition"
    evidence: "scripts/yuan-provenance.py:153-240 maps from path+heading substring only and defaults every unmatched clause to software-delivery; 450/1701 clauses use legacy-default-software-delivery and no legacy clause maps to Core"
    expectation: "Every legacy clause has an explicit reviewed disposition and exact destination/proof; unknown clauses fail closed as unmapped"
  - violation: "M7-B02: source line ranges are mechanically inaccurate and the verifier does not reject them"
    evidence: "Independent recomputation found 56 @preamble records with line_start > line_end and 61 @file records whose line_end is one past EOF"
    expectation: "Every source range is valid and independently recomputed; invalid or out-of-range coordinates make verification fail"
  - violation: "M7-B03: unique legacy facts are not preserved by the declared destinations"
    evidence: "1046 clauses point only to six short Extension files without target anchors; all 12 docs/anti-patterns.md clauses point to a ten-case catalog that omits multiple AP entries; the whole 312-line PTG runner is declared obsolete with Core conformance.py as a non-equivalent replacement"
    expectation: "Destination content or content-addressed retention must preserve each unique rule/example/exception, and obsolete proof must be semantically sufficient"
  - violation: "M7-B04: scope completeness is actor-editable and not independently fail-closed"
    evidence: "Removing docs/knowledge from include_roots in memory still passes discover(); 9 files disappear because required_families does not bind that root. The same gap exists for .yuan/adapters and .yuan/migration, while .gitignore and .workbuddy are neither mapped nor explicitly excluded"
    expectation: "A frozen independent inventory/policy must reject removed normative families and require an explicit disposition for every tracked or declared out-of-band file"
  - violation: "M7-B05: commit 8513dae is not a self-contained reproducible provenance revision"
    evidence: "The manifest binds current uncommitted bytes for AGENTS.md plus six dirty contracts and includes untracked .yuan/rules/test-integrity.md; those bytes are absent from the reviewed commit, so a clean checkout cannot reproduce 177 files / 1701 clauses"
    expectation: "Bind protected dirty sources through immutable M0a snapshots or an explicit external-source receipt so the reviewed commit can reproduce the same inventory without staging user changes"
advisory:
  - item: "The six Extension documents themselves respect the frozen Core boundary"
    reason: "No new primitive/result was found and they explicitly deny redefining COMPLETE or runtime authority; this positive result does not cure provenance failures"
evidence:
  - artifact_ref: "scripts/yuan-provenance.py"
    line: 153
    note: "Default and substring-only mapping implementation"
  - artifact_ref: ".yuan/extensions/provenance/clause-manifest.json"
    line: 1
    note: "Independent full-manifest hash/range/target audit"
  - artifact_ref: ".yuan/extensions/fixtures/legacy-anti-patterns.json"
    line: 1
    note: "Fixture catalog does not retain all mapped AP clauses"
  - artifact_ref: ".yuan/extensions/provenance/scope-policy.json"
    line: 1
    note: "Scope authority and required-family gap"
  - artifact_ref: ".yuan/extensions/README.md"
    line: 5
    note: "Extension boundary passed"
```

## Mechanical reproduction

```text
python -B scripts/yuan-provenance.py verify
PASS coverage=100.00% files=177 clauses=1701 links=PASS hashes=PASS
```

The command proves that generated artifacts equal the output of the same
generator. It does **not** prove semantic provenance:

| Independent check | Result |
|---|---:|
| Source SHA-256 mismatches | 0 |
| Clause SHA-256 mismatches | 0 |
| Missing target paths | 0 |
| Invalid `line_start > line_end` ranges | **56** |
| Whole-file `line_end` off-by-one ranges | **61 / 62** |
| Default catch-all mappings | **450 / 1,701** |
| Legacy clauses mapped to Core | **0** |
| Files silently removable with `docs/knowledge` policy deletion | **9** |

## Scope audit

The positive include roots correctly keep active Workspace state, archives,
event/evidence journals, `.yuan-shadow`, and repository-level tests outside the
legacy normative corpus. Core candidate tests are deliberately included with
Core. However, scope completeness is self-attested:

- `discover()` checks only families still named by the actor-edited policy.
- `.yuan/adapters`, `.yuan/migration`, and `docs/knowledge` are include roots
  but are absent from `required_families`.
- Most explicit include files are not independently frozen.
- `.gitignore` and ignored `.workbuddy` runtime memory are not represented in
  `excluded_inventory`, despite the report claiming exclusions are enumerated.

In-memory adversarial probe:

```text
baseline 177; without docs/knowledge 168; removed 9; no exception
```

## Provenance and preservation audit

The manifest is a content partition plus category heuristic, not a semantic
crosswalk:

- Mapping examines only `path + heading`; it never reads the clause body.
- An injected heading `Core COMPLETE may be self-declared by LLM` in
  `AGENTS.md` is still categorized as optional software-delivery advice.
- `scripts/build-graph.py` is mapped to UI because the substring `ui` occurs in
  `build`; `scripts/query-graph.py` falls through to software delivery.
- `docs/policies/write-policy.md` is routed to software delivery although it is
  Knowledge governance.
- 450 unmatched clauses receive a success disposition instead of remaining
  unmapped.
- Non-Markdown files are single coarse clauses, including
  `scripts/yuan_shadow_support.py` (1,269 lines), `bin/yuanforge-init` (678),
  `scripts/yuan-provenance.py` (448), and `scripts/pre-commit` (259).

`docs/anti-patterns.md` contains unique entries such as
`AP-CONTRACT-001`, `AP-FRAMEWORK-002`, `AP-FRAMEWORK-004`,
`AP-FRAMEWORK-005`, `AP-CONCURRENT-006`, and `AP-ENV-008`. All clauses map to
the fixture catalog, but the catalog has no content-bound case for those facts.
This contradicts PIT-004 and cannot justify later tombstoning.

The obsolete proof for `scripts/run-ptg-cal-check.py` correctly identifies its
zero-selection false-green condition. It incorrectly treats the entire file as
one obsolete clause, discarding potentially reusable scan/drift/report logic,
and names Core candidate conformance as the replacement even though it does not
execute application PTG/CAL assertions. `validate_manifest()` checks only that
proof strings are non-empty; it does not resolve or validate replacement or
fixture semantics.

## Extension boundary audit

The six Extension documents pass this axis:

- inputs are public Core records/protocol;
- outputs are authoring advice or Evidence;
- fixed roles, phases, TDD order, review counts, and platform mappings remain
  optional;
- none defines a seventh result or a second completion/authority reducer.

This is independent of the failed provenance axis and must remain intact during
task-010-r1.

## Database

Not applicable: task-010 changes no database schema, migration, or query.

## Performance

The 27,237-line generated manifest is acceptable only if it carries trustworthy
provenance. The current approach performs linear file/hash work, but its
semantic value is insufficient; performance is not the blocking concern.

## Code quality and organization

`scripts/yuan-provenance.py` is 448 source lines and combines discovery,
parsing, semantic routing, artifact generation, link validation, and CLI
handling. More importantly, verification reuses the exact author mapping
function, so it cannot independently detect a wrong disposition. Split/freeze
inventory, explicit mapping data, structural validation, and semantic review
lanes before considering style refactors.

## Rule-chain audit

| Rule | Status | Evidence |
|---|---|---|
| Genesis/Core freeze | PASS on Extension boundary; FAIL on provenance trust | Core semantics were not expanded, but no legacy clause is explicitly linked to Core |
| M7 Plan Gate | FAIL | “100% destination, unique knowledge zero loss” is not proven |
| PIT-003 | PASS | Runtime/archive state is mostly kept outside normative scope |
| PIT-004 | FAIL | Unique AP facts and whole-file script content are summarized away |
| verdict protocol | PASS | This report supplies blocking/evidence/expectation fields |
| test integrity | FAIL | Generator and verifier share the same mutable mapping and scope policy; no independent held-out semantic lane |

## Adversarial scenarios

1. **Scope deletion:** remove `docs/knowledge` from the in-memory policy.
   Discovery succeeds and silently removes nine sources.
2. **Contradictory clause:** pass an unsafe `AGENTS.md` heading asserting LLM
   self-completion to `mapping()`. It receives a valid software-delivery
   disposition.
3. **Boundary/range:** inspect frontmatter preambles and newline-terminated
   whole files. Verification still passes 117 inaccurate line ranges.
4. **Volume:** inspect large non-Markdown inputs. Thousands of heterogeneous
   lines receive one disposition, so 100% byte coverage conceals semantic
   under-review.

## Required correction

Return `task-010-r1` to Doc Engineer:

1. freeze an independent exhaustive source inventory, including explicit
   exclusions and protected dirty-source receipts;
2. replace keyword/default routing with an explicit per-clause mapping where
   unknown is unmapped/fail;
3. point every mapping to an exact target anchor/content hash or a
   content-addressed retained source;
4. preserve every unique rule/example/exception and split mixed/large
   non-Markdown files into semantic records;
5. correct and independently validate all line/byte ranges;
6. validate obsolete replacement/fixture references and semantic sufficiency;
7. add held-out negative tests for scope shrink, default catch-all,
   contradictory headings, invalid ranges, missing target anchors, and
   non-reproducible dirty sources.

M8 remains blocked until the same independent review is rerun against r1.
