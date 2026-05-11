# Backwards-compatible re-exports.
# New code should import from seedwork.infrastructure.outbox directly.
from seedwork.infrastructure.outbox import (
    InMemoryIntegrationEventOutboxRepository as InMemoryOutboxRepository,
)
from seedwork.infrastructure.outbox import (
    OutboxIntegrationEventPublisher,
)

__all__ = [
    "InMemoryOutboxRepository",
    "OutboxIntegrationEventPublisher",
]
