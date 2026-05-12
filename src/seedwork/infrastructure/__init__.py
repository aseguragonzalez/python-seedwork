from seedwork.infrastructure.command_bus_builder import CommandBusBuilder
from seedwork.infrastructure.deferred_domain_event_bus import DeferredDomainEventBus
from seedwork.infrastructure.domain_event_coordinator_command_bus import (
    DomainEventCoordinatorCommandBus,
)
from seedwork.infrastructure.domain_event_flush_command_bus import (
    DomainEventFlushCommandBus,  # backwards-compat alias
)
from seedwork.infrastructure.domain_event_publishing_repository import (
    DomainEventPublishingRepository,
)
from seedwork.infrastructure.in_memory_integration_event_publisher import (
    InMemoryIntegrationEventPublisher,
)
from seedwork.infrastructure.in_memory_repository import InMemoryRepository
from seedwork.infrastructure.in_memory_task_scheduler import InMemoryTaskScheduler
from seedwork.infrastructure.outbox import (
    InMemoryIntegrationEventOutboxRepository,
    InMemoryTaskOutboxRepository,
    IntegrationEventOutboxRecord,
    IntegrationEventOutboxRepository,
    OutboxIntegrationEventPublisher,
    OutboxStatus,
    OutboxTaskScheduler,
    TaskOutboxRecord,
    TaskOutboxRepository,
)
from seedwork.infrastructure.outbox_integration_event_publisher import (
    InMemoryOutboxRepository,  # backwards-compat alias
)
from seedwork.infrastructure.query_bus_builder import QueryBusBuilder
from seedwork.infrastructure.registry_command_bus import RegistryCommandBus
from seedwork.infrastructure.registry_query_bus import RegistryQueryBus
from seedwork.infrastructure.registry_task_bus import (
    BackgroundTaskRecord,
    InMemoryTaskQueue,
    RegistryTaskBus,
)
from seedwork.infrastructure.transactional_command_bus import TransactionalCommandBus

__all__ = [
    # command buses
    "CommandBusBuilder",
    "DeferredDomainEventBus",
    "DomainEventCoordinatorCommandBus",
    "DomainEventFlushCommandBus",  # backwards-compat alias
    "DomainEventPublishingRepository",
    "RegistryCommandBus",
    "TransactionalCommandBus",
    # query buses
    "QueryBusBuilder",
    "RegistryQueryBus",
    # repositories
    "InMemoryRepository",
    # integration event publishers
    "InMemoryIntegrationEventPublisher",
    "OutboxIntegrationEventPublisher",
    # outbox
    "InMemoryIntegrationEventOutboxRepository",
    "InMemoryOutboxRepository",  # backwards-compat alias
    "InMemoryTaskOutboxRepository",
    "IntegrationEventOutboxRecord",
    "IntegrationEventOutboxRepository",
    "OutboxStatus",
    "OutboxTaskScheduler",
    "TaskOutboxRecord",
    "TaskOutboxRepository",
    # background tasks
    "BackgroundTaskRecord",
    "InMemoryTaskQueue",
    "InMemoryTaskScheduler",
    "RegistryTaskBus",
]
