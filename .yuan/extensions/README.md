# Yuan Extensions 0.1

Extensions are optional engineering practices around Yuan Core. They are not a
second runtime.

## Boundary

Every extension:

1. consumes only the public Core contract in
   [`../core/0.1/protocol.md`](../core/0.1/protocol.md) and the four public
   record schemas beside it (`Work Contract`, `Run Memory`, `Attempt`,
   `Evidence`);
2. may provide Work Contract authoring advice (including verifier recipes or
   Adapter descriptor advice) or immutable Evidence, and no other authoritative
   output;
3. may not add a Core primitive, add a Tick result, redefine `COMPLETE`, write
   the runtime authority directly, or make itself a prerequisite of Core;
4. must be explicitly selected by a Work Contract before its advice or
   verifier recipe applies;
5. must return failure, unsupported capability, or Evidence through Core
   mechanisms instead of inventing a parallel status.

The six result names and completion predicate remain exclusively defined by
Core. Extension reviews, tests, documents, and platform checks are observations;
they become completion-relevant only through a verifier binding in the active
Work Contract and a valid Evidence record.

## Catalog

| Extension | Optional concern |
|-----------|------------------|
| [software-delivery](software-delivery.md) | planning, review profiles, bounded delivery, release claims |
| [testing](testing.md) | verifier recipes, held-out checks, integrity diff, real-environment checks |
| [docsos](docsos.md) | durable docs memory, templates, projections, link verification |
| [knowledge](knowledge.md) | advisory long-term knowledge and preservation |
| [ui](ui.md) | visual, interaction, accessibility, and screenshot verifier recipes |
| [platform-adapters](platform-adapters.md) | Protocol-over-Platform capability mapping and conformance |

## Provenance

Legacy normative sources remain byte-for-byte in place during M7. Their
mechanical clause map is described in
[`provenance/README.md`](provenance/README.md). A summary in an Extension never
authorizes deletion of the source clause. Tombstoning remains a later,
separately authorized operation.
