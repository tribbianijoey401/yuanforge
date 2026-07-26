# Software Delivery Extension

## Contract

This extension consumes the public Work Contract and Evidence schemas. It emits
only authoring advice and verifier Evidence. It does not define a Task runtime,
Goal runtime, mandatory role graph, Tick result, completion predicate, or
authority.

## Work authoring advice

A software-delivery Work may declare:

- a plan, dependency hints, risk, non-goals, budgets, and rollback boundaries;
- optional actor/checker role profiles and optional phase or review recipes;
- side effects that need authorization and the evidence expected before them;
- a finite retry or correction budget for every repeated strategy.

Roles, phases, DAGs, TDD ordering, commit granularity, and review counts are
profiles, not Core invariants. Select them only when evaluation shows a net
benefit for the Work.

## Bounded convergence

Every delivery recipe must state its exit condition, attempt budget, stagnation
condition, and escalation target in the Work Contract. Repeating the same
strategy with the same relevant inputs and no new Evidence is not progress.
Exhaustion produces no success claim; Core alone reduces the resulting state.

## Independent delivery claims

Delivery claims are separate predicates with separate Evidence:

```text
implemented → locally verified → committed → pushed/PR → merged
            → deployed → live verified → knowledge closed → cleaned
```

No arrow is implied by the previous state. In particular, `merged` is not
`deployed`, and `deployed` is not `live verified`. A recipe may omit
inapplicable states, but the Work must say why and may not report an unobserved
state.

## Review recipe

Reviews are optional verifier profiles. A useful review:

- reads the Work acceptance criteria, relevant contract, artifact diff, and
  verifier Evidence;
- separates blocking correctness/contract violations from advisory ideas;
- supplies evidence for every verdict;
- has a bounded correction loop;
- never overrides a deterministic failing verifier.

The review output is Evidence only when the Work pre-binds an appropriate
review verifier.
