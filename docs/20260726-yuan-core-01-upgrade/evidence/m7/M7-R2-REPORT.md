# task-010 M7 r2 Semantic Provenance Binding

> Role: Doc Engineer
> Frozen source revision: `c1fd815a85395351e7ebc23e3ff72507326977f2`
> Reviewed registry SHA-256: `4e8d974409bf0ad2bd66df17039c8dee12b6fca03a0e2860ed5ac865615823d4`
> Verdict: `PASS — author r2 complete; independent re-review required`

## M7-B06 closure

The r1 disposition map proved byte preservation but did not independently
constrain whether a disposition and its semantic target were related. r2
replaces it with a reviewed semantic registry. Every record binds:

- exact source identity and byte range;
- disposition and target family;
- exact target path, anchor, and hash;
- record-specific source and target claims;
- a semantic relation (`preserved`, `refined`, `superseded`, `fixture`, or
  `obsolete`).

The target-family registry independently enumerates valid Core and Extension
anchors. The verifier rejects category flips, cross-family targets, registry
drift, and changes relative to the reviewed registry hash. Seven audit-critical
misroutes are fixed and frozen as independent assertions.

The malformed-fence workflow clause at lines 259–593 is represented by 21
contiguous atomic records. The verifier checks their exact line starts, family
assignments, byte coverage, hashes, and retained parent binding.

## Coverage

| Metric | Value |
|--------|------:|
| Frozen tracked inventory | 294 |
| Out-of-band M0 sources | 2 |
| Included source files | 177 |
| Source clauses | 2,207 |
| Semantic records | 2,227 |
| Unmapped source clauses | 0 |
| Legacy clauses bound to Core | 12 |
| Anti-pattern fixtures | 8 |
| Obsolete PTG functions | 1 |

Target-family counts are `core=297`, `testing=415`, `docsos=366`,
`knowledge=751`, `ui=49`, `software-delivery=285`,
`platform-adapters=55`, `fixture=8`, and `obsolete=1`.

## Verification

```text
python -B scripts/yuan-provenance.py generate
PASS files=177 clauses=2207 semantic_records=2227 unmapped=0

python -B scripts/verify-yuan-provenance.py \
  --semantic-registry-sha256 4e8d974409bf0ad2bd66df17039c8dee12b6fca03a0e2860ed5ac865615823d4
PASS source_clauses=2207 semantic_records=2227 unmapped=0

python -B tests/provenance/test_m7_held_out.py -q
Ran 11 tests — OK
```

Regression results:

```text
py_compile:                  PASS
M1 bootstrap:               31/31 PASS
Core author:                35/35 PASS
M3 independent held-out:    30/30 PASS
M4 shadow migration:        10/10 PASS
M5 canary:                   1/1 PASS
M6 adapter conformance:      8/8 PASS
old Genesis trust root:      80 checks / 7 cases PASS
M0a protected dirty:         10/10 hashes PASS
```

No Core file, legacy normative source, authority pointer, or protected user
dirty file was modified by this repair. A detached clean checkout at `a4cb165`
received only the candidate staged diff. Author generation, independent
verification, and all 11 negative tests passed there; its generated outputs
matched the working candidate byte-for-byte:

| Artifact | SHA-256 |
|----------|---------|
| `scope-manifest.json` | `50e2ea028cf2fbb9092c85188b3e03a13b86b0e69ba1456ecbadc4dbde47e895` |
| `clause-manifest.json` | `4e8d974409bf0ad2bd66df17039c8dee12b6fca03a0e2860ed5ac865615823d4` |
| `REPORT.md` | `1dc1cce624efb19f6b7052ce2fca20ee3944a69bcfc628442358f9225e58f571` |
| `inventory.lock.json` | `cbe645f8c50291dca352cefcd461a3300d635c2a87011592383d00cc847a1f34` |
| `semantic-registry.json` | `4e8d974409bf0ad2bd66df17039c8dee12b6fca03a0e2860ed5ac865615823d4` |
| `semantic-registry.sha256` | `ff19a1e57b3585a5eb2771871f3b5729ca725490d3c2c60f28822fa1acce2bbd` |
| `target-family-registry.json` | `3f5c8a11e3d59d5352a20db8a2cb3919405b9cf398df0ddb7ea907ad969e535c` |
| `dirty-source-receipt.json` | `cc773b7073ae7cb85ee2d081e6e6febe50deb2fd973a5b60cdad22708666bb0f` |
