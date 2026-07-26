# task-010 M7 r1 Explicit and Reproducible Provenance

> Role: Doc Engineer
> Frozen source revision: `c1fd815a85395351e7ebc23e3ff72507326977f2`
> Verdict: `PASS — author r1 complete; independent re-review required`

## Blocker closure

| Blocker | Closure |
|---------|---------|
| M7-B01 | Replaced keyword/default classification with an exhaustive disposition map keyed by exact `source + anchor + clause_sha256`. Unknown tuples are emitted as `UNMAPPED` and fail generation. |
| M7-B02 | Markdown ranges are inclusive and EOF-safe; empty preambles are not emitted. Python uses top-level AST units, shell sources use functions/sections, and other structured or opaque sources are retained as explicit whole-file units. The independent verifier recomputes every range and hash. |
| M7-B03 | Every clause has an exact content-addressed retained blob. All eight named legacy anti-patterns are retained as exact negative fixtures. PTG is split by function; only the false-green `generate_report` function is obsolete-with-proof. |
| M7-B04 | `inventory.lock.json` freezes all 294 tracked paths plus two out-of-band M0 sources with explicit include/exclude decisions and reasons. Required families and exclusions are independently enforced; scope shrink fails. |
| M7-B05 | The eight tracked-dirty and two untracked M0 sources have immutable content-addressed snapshots and a receipt. A detached clean checkout reproduced all generated outputs byte-for-byte without access to the dirty originals. |

## Frozen scope and coverage

| Metric | Value |
|--------|------:|
| Frozen tracked inventory | 294 |
| Out-of-band M0 sources | 2 |
| Included source files | 177 |
| Included source bytes | 1,407,492 |
| Semantic clauses | 2,207 |
| Explicitly mapped | 2,207 |
| Unmapped | 0 |
| Coverage | 100.00% |

Disposition counts are `core=297`, `extension=1,115`, `knowledge=729`,
`fixture=65`, and `obsolete-with-proof=1`. Twelve legacy clauses bind exact
Core anchors. Eight anti-pattern fixtures and one PTG obsolete function are
independently verified.

## Independent and clean-checkout verification

```text
python -B scripts/yuan-provenance.py generate
PASS files=177 clauses=2207 mapped=2207 unmapped=0

python -B scripts/verify-yuan-provenance.py
PASS tracked_inventory=294 out_of_band=2 included_sources=177
     clauses=2207 mapped=2207 unmapped=0 legacy_to_core=12
     anti_patterns=8 ptg_obsolete_functions=1 dirty_snapshots=10

python -B tests/provenance/test_m7_held_out.py -q
Ran 6 tests — OK
```

The six held-out negatives reject scope shrink, removed explicit mapping,
contradictory headings, invalid ranges, missing destinations, and missing dirty
source snapshots. The verifier does not import or call the author generator.

A detached worktree at the frozen source revision was patched only with the
candidate staged diff. Author generation, independent verification, and all six
negative tests passed there. The following generated artifact hashes were
identical between the dirty source workspace and the clean checkout:

| Artifact | SHA-256 |
|----------|---------|
| `scope-manifest.json` | `50e2ea028cf2fbb9092c85188b3e03a13b86b0e69ba1456ecbadc4dbde47e895` |
| `clause-manifest.json` | `a3ee1d290bd5d949b2fed1123315badfdcd9d001ae3b01c7b01be38caa5f0429` |
| `REPORT.md` | `0dd24b4fa62ac03d95b607180213a23aa1154e09ba0b4d701ae488c146d895df` |
| `inventory.lock.json` | `cbe645f8c50291dca352cefcd461a3300d635c2a87011592383d00cc847a1f34` |
| `disposition-map.json` | `f0284469a582ba8a204d2cf2807b3b7df67d46742ed61ffbf4f46fecfc427bf3` |
| `dirty-source-receipt.json` | `cc773b7073ae7cb85ee2d081e6e6febe50deb2fd973a5b60cdad22708666bb0f` |

## Regression and integrity

```text
py_compile:                  PASS
M1 bootstrap:               31/31 PASS
Core author:                35/35 PASS
M3 independent held-out:    30/30 PASS
M4 shadow migration:        10/10 PASS
M5 canary:                   1/1 PASS (13 internal checks)
M6 adapter conformance:      8/8 PASS
old Genesis trust root:      80 checks / 7 cases PASS
M0a protected dirty:         10/10 hashes PASS
```

No Core, legacy normative source, authority pointer, or protected user dirty
file was staged or modified by this repair.
