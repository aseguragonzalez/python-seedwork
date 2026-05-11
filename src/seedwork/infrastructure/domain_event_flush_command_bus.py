# Backwards-compatible re-export. Use DomainEventCoordinatorCommandBus instead.
from seedwork.infrastructure.domain_event_coordinator_command_bus import (
    DomainEventCoordinatorCommandBus as DomainEventFlushCommandBus,
)

__all__ = ["DomainEventFlushCommandBus"]
