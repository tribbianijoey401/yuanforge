# Quality Audit: task-010-r2 / commit 619eef9

> Reviewer: independent Quality Auditor
> Reviewed revision: `619eef9875c50c312c043f7bdf12c7331a336c04`
> Reviewed semantic registry SHA-256: `4e8d974409bf0ad2bd66df17039c8dee12b6fca03a0e2860ed5ac865615823d4`
> Timestamp: 2026-07-27 03:14 +08:00
> Result: **PASS — M7-B01–B06 closed; task-011/M8 may consume this frozen Evidence**

```yaml
verdict: pass
blocking: []
advisory: []
evidence:
  - artifact_ref: ".yuan/extensions/provenance/semantic-registry.json"
    line: 1
    note: "2,227 reviewed semantic records for 2,207 source clauses; SHA-256 4e8d974409bf0ad2bd66df17039c8dee12b6fca03a0e2860ed5ac865615823d4"
  - artifact_ref: "scripts/yuan_provenance_verify.py"
    line: 323
    note: "Independent verifier binds registry pin, reviewed external hash, manifest identity, family registry, exact targets, claims, and compound coverage"
  - artifact_ref: "tests/provenance/test_m7_held_out.py"
    line: 140
    note: "Original B01–B05 probes and B06 category/target/family/drift/compound attacks all reject"
  - artifact_ref: "docs/20260726-yuan-core-01-upgrade/evidence/m7-review/M7-APPROVAL.json"
    line: 1
    note: "Machine-readable M8 upstream approval locks the reviewed registry hash"
```

## M8 upstream trust input

M8 must consume, record, and verify this exact value before changing authority:

```text
4e8d974409bf0ad2bd66df17039c8dee12b6fca03a0e2860ed5ac865615823d4
```

Required pre-switch command:

```text
python -B scripts/verify-yuan-provenance.py --semantic-registry-sha256 4e8d974409bf0ad2bd66df17039c8dee12b6fca03a0e2860ed5ac865615823d4
```

The repository-local `semantic-registry.sha256` is an integrity pin, not an
independent review root: an actor can change both a registry and its local pin.
The hash in this report and `M7-APPROVAL.json` is therefore a mandatory M8
upstream input. An M8 authority receipt that omits it or invokes the verifier
without `--semantic-registry-sha256` does not satisfy this approval.

## Clean-checkout reproduction

A fresh local clone was checked out at exactly `619eef9`; it contained no user
dirty or untracked source bytes.

```text
python -B scripts/verify-yuan-provenance.py \
  --semantic-registry-sha256 4e8d974409bf0ad2bd66df17039c8dee12b6fca03a0e2860ed5ac865615823d4

PASS tracked_inventory=294 out_of_band=2 included_sources=177
     source_clauses=2207 semantic_records=2227 unmapped=0
     legacy_to_core=12 anti_patterns=8
     ptg_obsolete_functions=1 dirty_snapshots=10

python -B tests/provenance/test_m7_held_out.py -q
Ran 11 tests — OK

python -B scripts/yuan-provenance.py generate
PASS files=177 clauses=2207 semantic_records=2227 unmapped=0
git status --short
<empty>
```

Regenerated hashes:

| Artifact | SHA-256 |
|---|---|
| `semantic-registry.json` | `4e8d974409bf0ad2bd66df17039c8dee12b6fca03a0e2860ed5ac865615823d4` |
| `clause-manifest.json` | `4e8d974409bf0ad2bd66df17039c8dee12b6fca03a0e2860ed5ac865615823d4` |
| `semantic-registry.sha256` | `ff19a1e57b3585a5eb2771871f3b5729ca725490d3c2c60f28822fa1acce2bbd` |
| `target-family-registry.json` | `3f5c8a11e3d59d5352a20db8a2cb3919405b9cf398df0ddb7ea907ad969e535c` |
| `scope-manifest.json` | `50e2ea028cf2fbb9092c85188b3e03a13b86b0e69ba1456ecbadc4dbde47e895` |
| `REPORT.md` | `1dc1cce624efb19f6b7052ce2fca20ee3944a69bcfc628442358f9225e58f571` |

## B01–B05 regression

| Blocker | Independent r2 result |
|---|---|
| B01 default/catch-all | **PASS** — unknown tuple remains `UNMAPPED`; no `mapping_rule`, `default`, `keyword`, or `review_rationale` field exists in any record |
| B02 invalid ranges | **PASS** — all included sources are independently re-split; inclusive range, byte coverage, source hash, clause hash, and retained bytes are checked |
| B03 unique-content loss | **PASS** — all records retain exact content-addressed bytes; AP8 and function-level PTG proof remain enforced |
| B04 shrinkable scope | **PASS** — frozen 294 tracked + 2 out-of-band inventory remains exhaustive; scope-shrink attack rejects |
| B05 dirty reproducibility | **PASS** — ten M0 dirty sources resolve through committed immutable snapshots; clean clone reproduces all outputs |

The first six held-out probes are unchanged in purpose and all reject:
scope shrink, missing mapping, contradictory unknown heading, invalid inclusive
range, missing retained destination, and missing dirty snapshot.

## B06 independent adversarial review

The author suite passed 11/11. A second probe was run without importing the
author generator, project tests, or verifier as a library; it mutated isolated
copies and invoked only the verifier CLI.

| Probe | Mutation | Result |
|---|---|---|
| Manifest identity | Compare registry and generated manifest bytes | **PASS** — byte-identical |
| Registry pin | Change registry + manifest but retain the old local pin | **REJECT** — `semantic registry hash pin mismatch` |
| Category flip | Change an Extension record to `core`, update manifest and local pin | **REJECT** — `disposition/target family mismatch` |
| Valid wrong target | Select another valid target in the same family, update manifest and local pin, retain reviewed external hash | **REJECT** — `semantic registry hash differs from reviewed value` |
| Cross-family | Relabel a software-delivery target as testing, update manifest and local pin | **REJECT** — `target family/path mismatch` |
| Registry/manifest drift | Change only a manifest claim | **REJECT** — `registry/manifest byte drift` |
| Compound deletion | Delete one atomic child, update registry, manifest, count, and local pin | **REJECT** — `compound clause family coverage mismatch` |

This closes the exact trust boundary exposed by M7-B06. Family constraints stop
category/cross-family changes; the external reviewed hash stops a different but
otherwise valid target within the same family.

## Full semantic-record audit

An additional ASCII-only independent checker inspected all records without
using project code:

```text
semantic_records:         2227
source_clause_keys:       2207
group sizes:              2206 x 1 record; 1 x 21 records
unique source_claims:     2227
unique claim pairs:       2227
semantic/Core targets:    483
exact retained targets:   1736
fixture targets:          8
heuristic fields:         0
failures:                 0
```

Every `source_claim` contains its exact source path, anchor, inclusive line
range, and a bounded content excerpt. Every Core/Extension `target_claim`
contains the exact target path and anchor. Retained targets use a shared
sentence shape, but each embeds the full record-specific source claim and
points to the byte-identical content-addressed destination; it explicitly does
not assert an unrelated summary. This is exact preservation, not the r1
file-level rationale template. Claim pairs are unique across all 2,227 records.

Target-kind distribution is:

- 297 frozen Core anchors;
- 186 exact Extension semantic anchors;
- 1,736 exact retained clauses, including the one obsolete clause;
- 8 exact fixture cases.

## Actual semantic corrections

The seven r1 misroutes are corrected and verifier-frozen:

| Source | Approved target |
|---|---|
| `iron-rules.md:90` TDD | testing / `verifier-recipe` |
| `iron-rules.md:160` 文档即代码 | DocsOS / `document-verification` |
| `iron-rules.md:374` 事实面独立验证 | testing / `actor-checker-separation` |
| `object-protocol.md:36` Knowledge | knowledge / `record-shape` |
| `object-protocol.md:61` Decision/ADR | knowledge / `promotion-advice` |
| `frontend-dev.md:24` TDD workflow | testing / `verifier-recipe` |
| `quality-auditor.md:57` 对抗式审查 | software-delivery / `review-recipe` |

Each sampled source claim quotes the specific legacy assertion; each target
claim quotes the selected Extension anchor rather than a family-wide generic
summary.

The formerly mixed `workflow-protocol.md:259-593` clause is now represented by
21 contiguous atomic semantic records. Their starts and reviewed families are
fixed independently; byte ranges cover the parent clause without gap or
overlap, and all children bind the same exact retained parent. Deleting any
child is fail-closed.

## Final Gate

M7 satisfies AC-08 at the reviewed registry hash above. M7-B01–B06 are closed.
Task-010 may be marked complete and task-011 may start, provided M8 treats
`M7-APPROVAL.json` as immutable upstream Evidence and records the same registry
hash in its authority-switch receipt.
