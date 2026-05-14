from bank_account.application.account_opened_integration_event import AccountOpenedIntegrationEvent
from bank_account.domain.events.account_opened import AccountOpened

from seedwork.application import DomainEventHandler, IntegrationEventPublisher


class AccountOpenedDomainEventHandler(DomainEventHandler[AccountOpened]):
    def __init__(self, publisher: IntegrationEventPublisher) -> None:
        self._publisher = publisher

    async def handle(self, event: AccountOpened) -> None:
        integration_event = AccountOpenedIntegrationEvent(
            type="bank_account.account_opened",
            version="1.0",
            aggregate_id=event.payload.account_id,
            payload={},  # derived from typed fields in __post_init__
            correlation_id=event.id,
            account_id=event.payload.account_id,
            owner="unknown",
            initial_balance=event.payload.initial_balance,
            currency=event.payload.currency,
        )
        await self._publisher.publish([integration_event])
