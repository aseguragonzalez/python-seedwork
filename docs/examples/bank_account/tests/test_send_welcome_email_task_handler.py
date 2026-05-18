from bank_account.application.account_opened_domain_event_handler import (
    AccountOpenedDomainEventHandler,
)
from bank_account.application.open_account.open_account_command import OpenAccountCommand
from bank_account.application.send_welcome_email.send_welcome_email_task import SendWelcomeEmailTask
from bank_account.application.send_welcome_email.send_welcome_email_task_handler import (
    SendWelcomeEmailTaskHandler,
)
from bank_account.composition_root import compose
from bank_account.domain.events.account_opened import AccountOpened, AccountOpenedPayload

from seedwork.testing import InMemoryIntegrationEventPublisher, InMemoryTaskScheduler


async def test_handler_schedules_welcome_email_task() -> None:
    scheduler = InMemoryTaskScheduler()
    publisher = InMemoryIntegrationEventPublisher()
    handler = AccountOpenedDomainEventHandler(publisher, scheduler)

    event = AccountOpened(
        aggregate_id="acc-1",
        payload=AccountOpenedPayload(initial_balance=100.0, currency="EUR"),
    )
    await handler.handle(event)

    assert len(scheduler.scheduled) == 1
    task = scheduler.scheduled[0]
    assert task.type == SendWelcomeEmailTask.TYPE
    assert task.payload["account_id"] == "acc-1"
    assert task.causation_id == event.id


async def test_execute_scheduled_runs_task_handler() -> None:
    scheduler = InMemoryTaskScheduler()
    scheduler.register(SendWelcomeEmailTask.TYPE, SendWelcomeEmailTaskHandler())
    publisher = InMemoryIntegrationEventPublisher()
    handler = AccountOpenedDomainEventHandler(publisher, scheduler)

    event = AccountOpened(
        aggregate_id="acc-1",
        payload=AccountOpenedPayload(initial_balance=100.0, currency="EUR"),
    )
    await handler.handle(event)

    await scheduler.execute_scheduled()

    assert len(scheduler.scheduled) == 0


async def test_compose_open_account_schedules_welcome_email_task() -> None:
    scheduler = InMemoryTaskScheduler()
    command_bus, _ = compose(task_scheduler=scheduler)

    await command_bus.dispatch(
        OpenAccountCommand(account_id="acc-1", initial_balance=100.0, currency="EUR")
    )

    assert len(scheduler.scheduled) == 1
    task = scheduler.scheduled[0]
    assert task.type == "send_welcome_email"
    assert task.payload["account_id"] == "acc-1"

    await scheduler.execute_scheduled()

    assert len(scheduler.scheduled) == 0
