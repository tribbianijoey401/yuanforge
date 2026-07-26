# Quality Audit: task-010-r1 / commit ff69740

> Reviewer: independent Quality Auditor
> Reviewed revision: `ff69740` (`fix(task-010): make provenance explicit and reproducible`)
> Timestamp: 2026-07-27 02:24 +08:00
> Result: **FAIL — M7-B01–B05 closed; new M7-B06 returns task-010-r2**

```yaml
verdict: fail
blocking:
  - violation: "M7-B06: explicit disposition and semantic destination are not independently constrained, so false provenance is accepted"
    evidence: "In a clean clone, changing a real Extension clause disposition to core while retaining an Extension semantic target was regenerated and accepted; replacing its exact semantic target with a different valid UI target was also accepted"
    expectation: "Verifier must enforce disposition-to-target-family invariants and an independently frozen clause-to-semantic-target review binding; wrong category or unrelated target must fail closed"
advisory:
  - item: "M7-B01–B05 are mechanically closed"
    reason: "Clean-checkout reproduction, frozen exhaustive inventory, 2207 independent range/hash checks, exact retained bytes, AP8, function-level PTG obsolete proof, dirty snapshots, and the original six negative cases all passed"
evidence:
  - artifact_ref: "scripts/yuan_provenance_verify.py"
    line: 373
    note: "Allowed disposition and target existence/hash are checked independently, but their semantic relationship is not"
  - artifact_ref: ".yuan/extensions/provenance/clause-manifest.json"
    line: 1
    note: "Current manifest contains actual coarse/misdirected semantic mappings"
  - artifact_ref: ".yuan/extensions/provenance/disposition-map.json"
    line: 1
    note: "2207 mappings use only nine repeated review-rationale templates"
  - artifact_ref: ".yuan/rules/iron-rules.md"
    line: 90
    note: "TDD clause maps to software-delivery/work-authoring rather than testing/verifier semantics"
```

## Independent clean-checkout reproduction

A fresh local clone at `ff69740` contained only committed bytes. In particular,
the original untracked `.yuan/rules/test-integrity.md` was absent, proving the
verification lane had to use the committed M0 snapshot.

```text
python -B scripts/verify-yuan-provenance.py
PASS tracked_inventory=294 out_of_band=2 included_sources=177
     clauses=2207 mapped=2207 unmapped=0 legacy_to_core=12
     anti_patterns=8 ptg_obsolete_functions=1 dirty_snapshots=10

python -B -m unittest discover -s tests/provenance -p "test_*.py" -v
Ran 6 tests — OK

python -B scripts/yuan-provenance.py generate
PASS files=177 clauses=2207 mapped=2207 unmapped=0

git status --short
<empty>
```

Regenerated hashes matched the committed author report:

| Artifact | SHA-256 |
|---|---|
| `scope-manifest.json` | `50e2ea028cf2fbb9092c85188b3e03a13b86b0e69ba1456ecbadc4dbde47e895` |
| `clause-manifest.json` | `a3ee1d290bd5d949b2fed1123315badfdcd9d001ae3b01c7b01be38caa5f0429` |
| `REPORT.md` | `0dd24b4fa62ac03d95b607180213a23aa1154e09ba0b4d701ae488c146d895df` |

## M7-B01–B05 closure

| Original blocker | Independent result | Evidence |
|---|---|---|
| B01 catch-all / false 100% | **CLOSED mechanically** | Unknown `source+anchor+hash` is unmapped; explicit map has 2,207 exact keys and generator contains no disposition fallback |
| B02 invalid coordinates | **CLOSED** | Independent script recomputed all 2,207 byte slices, inclusive ranges, source/clause hashes, and contiguous coverage: 0 failures |
| B03 unique-content loss | **CLOSED for preservation** | Every clause has a byte-identical content-addressed retained blob; AP8 and PTG function split are preserved |
| B04 shrinkable scope | **CLOSED** | Inventory exhaustively matches all 294 paths at frozen revision plus two fixed out-of-band entries; original scope-shrink negative is rejected |
| B05 dirty/non-reproducible | **CLOSED** | Ten M0 sources have committed immutable snapshots; clean clone reproduced all outputs without dirty originals |

All 2,207 retained destinations were independently compared byte-for-byte with
their source slices. Source SHA, clause SHA, destination SHA, range, and
coverage failures were all zero.

Non-Markdown partitioning is materially improved:

- Python and Python-shebang sources: 508 AST clauses plus 10 preambles;
- shell: 21 function/section clauses plus one preamble;
- structured/opaque whole-file records: 28, all content-addressed;
- only seven whole-file structured sources exceed 100 lines, primarily frozen
  Core schemas, CSV catalogs, and `docs/object-model.yaml`.

All eight named `docs/anti-patterns.md` entries have exact fixture-case targets
and exact retained source bytes. `scripts/run-ptg-cal-check.py` has twelve AST
records; only `py:function:generate_report:1` is
`obsolete-with-proof`. The other functions remain retained as Extension or
Fixture material.

## New adversarial variants

The original six negatives correctly reject scope shrink, missing mapping,
contradictory heading, invalid range, missing destination, and missing dirty
snapshot.

Two new variants expose an untested trust boundary:

### Variant A — category flip

1. Select a real mapping whose disposition is `extension`.
2. Change only its disposition to `core`.
3. Leave its semantic target pointing to `.yuan/extensions/...`.
4. Regenerate derived manifests.
5. Run the independent verifier.

Result:

```text
category-flip-extension-to-core: ACCEPTED
```

### Variant B — unrelated exact target

1. Select the same real clause.
2. Replace its semantic target with a different, existing UI Extension anchor
   and its correct hash.
3. Regenerate and independently verify.

Result:

```text
semantic-target-swap: ACCEPTED
```

The retained blob prevents byte loss but cannot prove the claimed category or
new semantic destination. Lines 373–398 of the verifier validate that:

- disposition is one of five allowed strings;
- retained bytes are exact;
- a semantic target, if supplied, exists and has the declared hash.

They do not validate that `core` points to Core, `extension` points to the
selected Extension family, or that the target corresponds to the source
clause. Thus an actor can alter the meaning of the 100% report and still receive
PASS.

## Actual mapping defects in ff69740

This is not only a hypothetical mutation. Risk-directed samples show the r1 map
is mostly an explicit file-level bulk classification:

| Source clause | Current semantic target | Expected family/target |
|---|---|---|
| `iron-rules.md:90-99` — TDD | software-delivery / `work-authoring-advice` | testing / verifier or actor-checker recipe |
| `iron-rules.md:160-172` — 文档即代码 | software-delivery / `work-authoring-advice` | DocsOS / state externalization or document verification |
| `iron-rules.md:374-384` — 事实面独立验证 | software-delivery / `work-authoring-advice` | testing / actor-checker separation |
| `object-protocol.md:36-39` — Knowledge 对象 | software-delivery / `work-authoring-advice` | Knowledge Extension |
| `object-protocol.md:61-80` — Decision/ADR | software-delivery / `work-authoring-advice` | Knowledge or DocsOS |
| `frontend-dev.md:24-34` — TDD workflow | software-delivery / `work-authoring-advice` | testing recipe |
| `quality-auditor.md:57-72` — 对抗式审查 | software-delivery / `work-authoring-advice` | software-delivery / `review-recipe` |

Additionally, malformed legacy fencing causes
`workflow-protocol.md:259-593` to become one 335-line clause containing Tester,
Knowledge promotion, multiple Loop types, platform dispatch, recovery, Human
Gates, and Gate schema. Assigning that mixed record only to
software-delivery/work-authoring is not credible clause-level provenance.

The distribution reinforces the finding:

```text
729 mappings: identical "knowledge" rationale
490 mappings: identical "software-delivery" rationale
342 mappings: identical "docsos" rationale
297 mappings: identical "core" rationale
...
```

Only nine rationale strings cover all 2,207 records. Exact retention makes
cleanup recoverable, but does not establish that each legacy clause has the
correct new home.

## Extension/Core boundary

The six Extension documents themselves still pass:

- no new Core primitive or seventh result;
- no redefinition of `COMPLETE`;
- no second runtime authority;
- Extension output remains advice or Evidence.

The new blocker concerns provenance truth, not Extension runtime semantics.

## Required task-010-r2 correction

1. Add fail-closed disposition-family validation:
   - `core` semantic targets must be frozen Core anchors;
   - `extension` targets must name the selected Extension and anchor;
   - `knowledge` targets must name Knowledge advice or an exact retained
     Knowledge source;
   - `fixture` and `obsolete-with-proof` must retain their existing exact
     fixture/proof rules.
2. Freeze an independent semantic-review table or policy, separate from the
   actor-authored disposition map, for all legacy clauses that claim a Core or
   Extension destination.
3. Replace the nine bulk rationale templates with clause-appropriate evidence
   or an explicit reviewed group whose membership is independently fixed.
4. Correct the sampled misroutes and audit all same-file bulk classifications.
5. Split mixed Markdown records caused by malformed fencing, or assign
   independently reviewed subranges so one record does not span unrelated
   semantic families.
6. Add the two accepted attacks as permanent negative tests, then rerun the
   original B01–B05 suite unchanged.

M8 remains blocked until r2 passes the same independent review.
