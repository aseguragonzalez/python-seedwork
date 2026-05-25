# python-seedwork

[![PyPI version](https://img.shields.io/pypi/v/python-seedwork)](https://pypi.org/project/python-seedwork/)
[![Python](https://img.shields.io/pypi/pyversions/python-seedwork)](https://pypi.org/project/python-seedwork/)
[![License: MIT](https://img.shields.io/pypi/l/python-seedwork)](https://github.com/aseguragonzalez/python-seedwork/blob/main/LICENSE)
[![CI](https://github.com/aseguragonzalez/python-seedwork/actions/workflows/ci.yml/badge.svg)](https://github.com/aseguragonzalez/python-seedwork/actions/workflows/ci.yml)

DDD and Hexagonal Architecture building blocks for Python.

## Goals

- **Unify design patterns.** Provide a shared vocabulary — entities, aggregates, value objects, domain events, CQRS buses — so every bounded context starts from the same foundation.
- **Keep domain logic pure.** The domain layer has zero framework or infrastructure imports. Business rules live in the domain; everything else lives in infrastructure.
- **Clear layer boundaries.** Protocols define contracts; implementations satisfy them structurally. The dependency direction is enforced: domain ← application ← infrastructure.

## Components

| Layer | Package | Components |
|---|---|---|
| Domain | `seedwork.domain` | `Entity`, `AggregateRoot`, `ValueObject`, `DomainEvent`, `DomainEventRecord`, `DomainError`, `Repository`, `UnitOfWork` |
| Application | `seedwork.application` | `Command`, `Query[TResult]`, `CommandHandler`, `QueryHandler`, `CommandBus`, `QueryBus`, `Result`, `DomainEventBusPublisher`, `DomainEventBusSubscriber`, `DomainEventBus`, `DomainEventHandler`, `BaseIntegrationEvent`, `IntegrationEvent`, `IntegrationEventPublisher`, `IntegrationEventHandler`, `BackgroundTask`, `TaskScheduler` |
| Infrastructure | `seedwork.infrastructure` | `RegistryCommandBus`, `RegistryQueryBus`, `TransactionalCommandBus`, `DomainEventCoordinatorCommandBus`, `CommandBusBuilder`, `QueryBusBuilder`, `DeferredDomainEventBus`, `DomainEventPublishingRepository`, `InMemoryRepository` |

All components are re-exported from the top-level `seedwork` package.

## Installation

```bash
pip install python-seedwork
```

Requires Python 3.12+. Ships a `py.typed` marker (PEP 561) — mypy and pyright pick up the inline types automatically.

## Documentation

- [Getting Started](getting-started.md) — Step-by-step guide: install, define a domain model, handle commands, wire buses.
- [Component Reference](component-reference.md) — Every abstract class, protocol, and infrastructure component.
- [Architecture](architecture.md) — Service building blocks: API, database, subscriber, publisher, worker, outbox, observability.
- [Best Practices](best-practices.md) — Design rules for domain components, application layer contracts, and event/task selection.
- [Coding Standards](coding-standards.md) — Conventions aligned with DDD and Clean Architecture, with do/don't guidelines.
