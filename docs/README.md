# python-seedwork — Documentation

This package provides DDD and Hexagonal Architecture building blocks for Python applications.

## Contents

- [Getting started](getting-started.md) — Step-by-step guide: install, define a domain model, handle commands, wire buses.
- [Component reference](component-reference.md) — Every abstract class, protocol, and infrastructure component.
- [Best practices](best-practices.md) — How to use the package effectively in your project.
- [Coding standards](coding-standards.md) — Conventions aligned with DDD and Clean Architecture, with do/don't guidelines.

## Complete working example

A full, self-contained example that exercises all building blocks lives in the test suite:

- **[examples/bank_account/](../examples/bank_account/)** — Domain (aggregate root, value objects, domain events, repository interface, errors). Use it as a reference when building a new bounded context.

## Quick links

- [Domain layer](component-reference.md#domain-layer) — Entity, AggregateRoot, ValueObject, DomainEvent, Repository, UnitOfWork, Errors.
- [Application layer](component-reference.md#application-layer) — Commands, Queries, Result, Domain Events.
- [Infrastructure layer](component-reference.md#infrastructure-layer) — Bus implementations, decorators, builders.
