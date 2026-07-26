# Clause Provenance

M7 maps every frozen legacy clause to exactly one disposition:

```text
core | extension | knowledge | fixture | obsolete-with-proof
```

## Frozen inputs

[`inventory.lock.json`](inventory.lock.json) enumerates all 294 files tracked by
the frozen source revision plus both M0 out-of-band files. Every entry has an
explicit `include` or `exclude` decision and reason. Required families include
the repository entrypoints, contracts, Core, specs, rules, document templates,
skills, platforms, Adapters, migration, protocols, templates, policies,
Knowledge, key scripts, initializer, VERSION, and `.gitignore`.

The eight tracked dirty and two untracked M0 sources are reproduced from the
content-addressed files in `sources/`; their independent bindings are in
[`dirty-source-receipt.json`](dirty-source-receipt.json). Original dirty paths
remain untouched and unstaged.

[`disposition-map.json`](disposition-map.json) is an explicit reviewed map keyed
by source path, semantic anchor, and clause SHA-256. The generator contains no
keyword, substring, default, or catch-all disposition. A new or changed clause
therefore becomes `UNMAPPED` and fails generation.

## Clause boundaries

- Markdown uses inclusive ATX-heading ranges outside fenced code. A preamble is
  emitted only when bytes exist before the first heading.
- Python and Python-shebang files use top-level AST functions, classes,
  imports, assignments, and module statements.
- Shell uses functions and named comment sections.
- Structured JSON/YAML/CSV and small opaque files are retained as an explicitly
  content-addressed whole-file source.

Every mapped clause points to an exact byte-identical blob in `retained/`.
Extension summaries are navigation only; the retained pack preserves unique
rules, examples, tables, exceptions, and legacy implementation details.

## Reproduce and verify

```text
python -B scripts/yuan-provenance.py generate
python -B scripts/verify-yuan-provenance.py
python -B -m unittest discover -s tests/provenance -p "test_*.py" -v
```

The independent verifier does not import the author generator. It independently
recomputes the frozen Git inventory, M0 source receipt, clause ranges/hashes,
explicit mapping coverage, retained destinations, target anchors/hashes,
anti-pattern fixtures, and obsolete proof.

Held-out negatives reject:

- inventory shrink;
- a missing explicit mapping/default route;
- a contradictory heading;
- an invalid inclusive range;
- a missing destination/target;
- a dirty source that cannot be reproduced.

## Exclusions

Workspace runtime state, archive/evidence/event journals, `.yuan-shadow`,
`.yuan-run`, `.workbuddy`, repository-level tests, caches, Git internals, and M7
generated outputs are explicitly excluded. Core candidate tests remain within
the frozen Core family. Exclusion preserves those artifacts; it does not delete
or weaken them.
