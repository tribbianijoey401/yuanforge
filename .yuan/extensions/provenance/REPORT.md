# M7 Semantic Clause Provenance Report

> Generated only from frozen source bytes and the reviewed semantic registry.

## Coverage

- frozen tracked inventory: 294
- out-of-band M0 sources: 2
- included source files: 177
- included source bytes: 1407492
- source clauses: 2207
- semantic records: 2227
- unmapped source clauses: 0
- coverage: 100.00%
- semantic registry SHA-256: `4e8d974409bf0ad2bd66df17039c8dee12b6fca03a0e2860ed5ac865615823d4`

## Dispositions

| Disposition | Clauses |
|-------------|--------:|
| `core` | 297 |
| `extension` | 1316 |
| `knowledge` | 605 |
| `fixture` | 8 |
| `obsolete-with-proof` | 1 |
| `UNMAPPED` | 0 |

## Target families

- `core`: 297
- `docsos`: 366
- `fixture`: 8
- `knowledge`: 751
- `obsolete`: 1
- `platform-adapters`: 55
- `software-delivery`: 285
- `testing`: 415
- `ui`: 49

## Relations

- `fixture`: 8
- `obsolete`: 1
- `preserved`: 2020
- `refined`: 198

## Trust boundary

- The generator never infers, classifies, or rewrites semantic review decisions.
- Unknown source+anchor+hash tuples fail as `UNMAPPED`.
- `clause-manifest.json` is byte-identical to `semantic-registry.json`.
- Every record binds a disposition, target family, exact target, source claim, target claim, and relation.
- Every mapped clause points to an exact content-addressed retained blob.
- Independent verification is performed by `scripts/verify-yuan-provenance.py`.
- Legacy sources and protected dirty paths remain untouched.
