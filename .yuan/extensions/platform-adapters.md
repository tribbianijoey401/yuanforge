# Platform Adapters Extension

## Contract

This extension implements “Protocol over Platform”: Core defines semantic
requirements; an Adapter declares how a platform supplies them. It consumes the
public Protocol and Port contract and emits only Adapter authoring advice or
conformance Evidence. A descriptor is a declarative part of that advice, not a
parallel authority. This extension cannot change Core semantics when a
capability is missing.

## Capability mapping

An Adapter must explicitly declare support for the minimum Port capabilities:

- bounded, stable, content-bound file enumeration/read and atomic compare-and-
  swap write;
- bounded, cancellable command execution with a structured receipt;
- one LLM proposal call that returns a structured receipt and does not execute
  the proposed action.

Every `supported` claim binds an executable implementation and hash. Missing
capability is `unsupported`, never an implicit fallback with weaker semantics.
The manual Reference Port is the baseline mapping; a platform-specific guide is
not proof of executable conformance.

## Conformance Evidence

Adapter validation should cover path escape, links/junctions, budget expansion,
timeout, malformed provider output, provider failure, descriptor drift, and
unsupported honesty. Its result is Evidence and cannot create a seventh Tick
result or independently declare Work complete.

## Version authority

`.yuan/VERSION` is the single source for the distributed framework version.
Initializers, manifests, skills, and user-facing output must read or be
mechanically checked against it; copied constants are caches and drift must fail
verification. Version agreement is a packaging fact, not completion proof for
an unrelated Work.
