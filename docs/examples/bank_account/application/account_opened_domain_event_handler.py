from bank_account.application.account_opened_integration_event import AccountOpenedIntegrationEvent
from bank_account.domain.events.account_opened import AccountOpened

from seedwork.application import DomainEventHandler, IntegrationEventPublisher


class AccountOpenedDomainEventHandler(DomainEventHandler[AccountOpened]):
    def __init__(self, publisher: IntegrationEventPublisher) -> None:
        self._publisher = publisher

    async def handle(self, event: AccountOpened) -> None:
        integration_event = AccountOpenedIntegrationEvent.from_domain_event(event)
        await self._publisher.publish([integration_event])
