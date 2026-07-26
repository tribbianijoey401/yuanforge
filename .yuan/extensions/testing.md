# Testing Extension

## Contract

This extension consumes Work Contract, Attempt, and Evidence records and emits
verifier recipes or Evidence. It does not add a Gate state, make TDD ordering a
Core rule, redefine the six Tick results, or decide `COMPLETE`.

## Verifier recipe

For each typed acceptance criterion, authoring advice should identify:

- the observable predicate and artifact/environment scope;
- a verifier revision frozen before the result is known;
- a positive case, a meaningful negative case, and a non-zero assertion count;
- freshness, timeout, parse, log, and failure-closed behavior;
- whether the check needs an isolated or real integration environment.

Mocks may support logic tests but cannot prove an external contract. Database,
network, filesystem, Adapter, deployment, and other physical claims require an
observation against the declared real or isolated environment. Contract
assertions must compare the declared contract with that environment rather than
simulate a function name or accept an empty test selection.

## Actor/checker separation

For high-risk or self-modifying Work, the checker should be independent from
the actor and should receive the acceptance criteria, relevant diff, contract,
and results without inheriting the actor's justification narrative. The
checker emits structured Evidence; it does not create a parallel completion
authority.

## Integrity and anti-gaming

Critical acceptance should use all applicable protections:

1. an author-inaccessible or independently frozen deterministic verifier;
2. held-out inputs or expectations;
3. a separate integrity diff for implementation versus tests, thresholds,
   fixtures, skips, `xfail`, hooks, baselines, and exemptions;
4. negative fixtures that prove known-bad, empty, zero-assertion, crash,
   unparseable, stale, and scope-escape cases fail closed.

Changing a validator and the candidate in one trust lane is not independent
proof. A passing command, a green author test, or a review statement is only an
observation until the bound Evidence satisfies Core validation.

## Selected regression fixtures

The content-bound inventory in
[`fixtures/legacy-anti-patterns.json`](fixtures/legacy-anti-patterns.json)
preserves representative failure modes found in legacy YuanForge. It is a
fixture catalog, not a new result model.
