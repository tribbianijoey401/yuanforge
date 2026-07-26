# Knowledge Extension

## Contract

Knowledge is optional advice. This extension consumes Core Evidence references
and emits authoring advice; it cannot alter Work, authorize actions, write Run
Memory, define Tick results, or serve as completion Evidence merely because a
claim exists.

## Record shape

A reusable claim should carry:

```text
claim
source_evidence
applicability
confidence
invalidation_condition
last_verified_against
```

A cold-start LLM may use such a claim as a search hint. Current Work,
current-environment observations, and valid bound Evidence take precedence.
Stale or unscoped claims remain advice and must not be promoted by repetition.

## Promotion advice

Promotion is a content-preserving editorial workflow:

1. extract a claim and retain its exact source pointer/hash;
2. validate it against current evidence and state its scope;
3. propose the knowledge record without changing runtime authority;
4. accept it only through the repository's separately authorized write path.

Optimization must not delete unique examples, tables, exceptions, or decision
details merely to shorten a document. A summary can coexist with the source
until clause provenance and cleanup authorization prove safe removal. This is
the retained lesson from `PIT-004`.

## Conflicts and invalidation

Conflicting claims are not averaged. Record the conflict, evidence on each side,
and the condition that would resolve it. Missing evidence, unknown provenance,
or an expired `last_verified_against` lowers confidence; it never becomes a
silent pass.
