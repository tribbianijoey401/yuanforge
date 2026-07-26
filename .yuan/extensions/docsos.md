# DocsOS Extension

## Contract

This extension consumes public Core schemas and emits authoring advice or
document-verifier Evidence. It cannot make Markdown authoritative over immutable
Work, Attempt, or Evidence sources, cannot write Run Memory directly, and
cannot redefine Core results or completion.

## State externalization

LLM memory is not durable. Intent, authorization, evidence pointers, active
failure hypotheses, pending side effects, and recovery instructions must be
externalized in bounded, addressable artifacts. Run Memory is a disposable
projection; human-readable task boards, dashboards, and session summaries
should be generated views when Core authority is active, not additional
writable truth sources.

Documents should be maps: keep the entrypoint short, point to canonical sources,
and load detail progressively. Repeating the same rule in multiple files
creates drift and should be replaced with a reference or a generated view.

## Template and runtime separation

Framework templates belong to `.yuan/docs/`. Project runtime state belongs to
the active runtime area selected by authority. A template must not contain a
project's live state, and a project status document must not silently become a
framework template. This preserves `PIT-003`.

## Document verification

Document checks may emit Evidence for:

- local link and anchor resolution;
- required schema/section presence;
- content hashes and generated-view freshness;
- explicit authority labels and no stale writable duplicate;
- UTF-8 and deterministic rendering where relevant.

Document presence or link validity alone never proves product completion.

## Preservation during migration

Summaries are indexes, not substitutes for unique source content. Before any
legacy source is removed, clause-level provenance must bind its original hash
to Core, Extension, Knowledge, Fixture, or Obsolete-with-proof. This preserves
`PIT-004`; actual tombstoning still requires the later cleanup authorization.
