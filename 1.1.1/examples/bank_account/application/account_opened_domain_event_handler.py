from bank_account.application.account_opened_integration_event import AccountOpenedIntegrationEvent
from bank_account.application.send_welcome_email.send_welcome_email_task import SendWelcomeEmailTask
from bank_account.domain.events.account_opened import AccountOpened

from seedwork.application import DomainEventHandler, IntegrationEventPublisher
from seedwork.application.background_tasks import TaskScheduler


class AccountOpenedDomainEventHandler(DomainEventHandler[AccountOpened]):
    def __init__(self, publisher: IntegrationEventPublisher, task_scheduler: TaskScheduler) -> None:
        self._publisher = publisher
        self._task_scheduler = task_scheduler

    async def handle(self, event: AccountOpened) -> None:
        integration_event = AccountOpenedIntegrationEvent.from_domain_event(event)
        await self._publisher.publish([integration_event])
        task = SendWelcomeEmailTask.from_domain_event(event)
        await self._task_scheduler.schedule(task)
