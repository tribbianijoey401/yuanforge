# UI Extension

## Contract

This extension supplies optional UI authoring advice and verifier recipes. It
consumes Work Contract and Evidence schemas and emits only advice or Evidence.
It does not require a UI Designer role, add review results, write authority, or
redefine Core completion.

## Work authoring advice

When a Work has a user interface, declare:

- target users, tasks, supported viewports, states, and content;
- visual references or design tokens that are actually authoritative;
- accessibility, keyboard, focus, contrast, motion, and touch requirements;
- loading, empty, error, permission, offline, and destructive-action states;
- screenshot or interaction environments and accepted tolerances.

Legacy visual rules and design-system references are a catalog. They apply only
when selected by the Work; style taste alone is not a blocker.

## Verifier recipes

Applicable verifiers may produce Evidence for:

- deterministic screenshots at declared viewport, font, theme, data, and
  browser revisions;
- semantic structure, accessible names, focus order, keyboard paths, contrast,
  reduced motion, and touch targets;
- interaction state coverage and absence of placeholder or fake controls;
- comparison to an approved reference with a declared tolerance.

A screenshot, reviewer opinion, or clean lint output cannot by itself prove all
UI acceptance criteria. Evidence remains scoped to the predicate it observed.
