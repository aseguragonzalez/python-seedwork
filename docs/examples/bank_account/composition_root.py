from bank_account.application.account_opened_domain_event_handler import (
    AccountOpenedDomainEventHandler,
)
from bank_account.application.deposit_money.deposit_money_command import DepositMoneyCommand
from bank_account.application.deposit_money.deposit_money_handler import DepositMoneyHandler
from bank_account.application.get_balance.get_balance_handler import GetBalanceHandler
from bank_account.application.get_balance.get_balance_query import GetBalanceQuery
from bank_account.application.open_account.open_account_command import OpenAccountCommand
from bank_account.application.open_account.open_account_handler import OpenAccountHandler
from bank_account.application.send_welcome_email.send_welcome_email_task import SendWelcomeEmailTask
from bank_account.application.send_welcome_email.send_welcome_email_task_handler import (
    SendWelcomeEmailTaskHandler,
)
from bank_account.domain.bank_account_repository import BankAccountRepository
from bank_account.domain.events.account_opened import AccountOpened
from bank_account.infrastructure.in_memory_bank_account_repository import (
    InMemoryBankAccountRepository,
)

from seedwork.application.commands import CommandBus
from seedwork.application.integration_events import IntegrationEventPublisher
from seedwork.application.queries import QueryBus
from seedwork.infrastructure import (
    CommandBusBuilder,
    DeferredDomainEventBus,
    DomainEventPublishingRepository,
    QueryBusBuilder,
    RegistryCommandBus,
    RegistryQueryBus,
)
from seedwork.testing import InMemoryIntegrationEventPublisher, InMemoryTaskScheduler


def build_command_bus(
    event_bus: DeferredDomainEventBus,
    repository: BankAccountRepository,
) -> CommandBus:
    registry = RegistryCommandBus()
    return (
        CommandBusBuilder(registry)
        .register(OpenAccountCommand, OpenAccountHandler(repository))
        .register(DepositMoneyCommand, DepositMoneyHandler(repository))
        .with_domain_event_coordination(event_bus)
        .build()
    )


def build_query_bus(repository: InMemoryBankAccountRepository) -> QueryBus:
    registry = RegistryQueryBus()
    return (
        QueryBusBuilder(registry).register(GetBalanceQuery, GetBalanceHandler(repository)).build()
    )


def compose(
    integration_publisher: IntegrationEventPublisher | None = None,
    task_scheduler: InMemoryTaskScheduler | None = None,
) -> tuple[CommandBus, QueryBus]:
    inner_repo = InMemoryBankAccountRepository()
    event_bus = DeferredDomainEventBus()
    publisher: IntegrationEventPublisher = (
        integration_publisher or InMemoryIntegrationEventPublisher()
    )
    scheduler = task_scheduler or InMemoryTaskScheduler()
    scheduler.register(SendWelcomeEmailTask.TYPE, SendWelcomeEmailTaskHandler())
    event_bus.subscribe(AccountOpened, AccountOpenedDomainEventHandler(publisher, scheduler))
    repository: BankAccountRepository = DomainEventPublishingRepository(inner_repo, event_bus)
    command_bus = build_command_bus(event_bus, repository)
    query_bus = build_query_bus(inner_repo)
    return command_bus, query_bus
