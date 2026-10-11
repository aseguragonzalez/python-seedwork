from bank_account.application.deposit_money.deposit_money_command import DepositMoneyCommand
from bank_account.application.open_account.open_account_command import OpenAccountCommand
from bank_account.application.withdraw_money.withdraw_money_command import WithdrawMoneyCommand
from bank_account.composition_root import compose

from seedwork.testing import InMemoryIntegrationEventPublisher


async def test_compose_open_account_publishes_integration_event() -> None:
    publisher = InMemoryIntegrationEventPublisher()
    command_bus, _ = compose(integration_publisher=publisher)

    await command_bus.dispatch(
        OpenAccountCommand(
            account_id="acc-1", owner_id="user-1", initial_balance=100.0, currency="EUR"
        )
    )

    assert len(publisher.published) == 1
    event = publisher.published[0]
    assert event.type == "bank_account.account_opened"
    assert event.aggregate_id == "acc-1"
    assert event.causation_id is not None
    assert event.payload["initial_balance"] == 100.0
    assert event.payload["currency"] == "EUR"


async def test_compose_deposit_money() -> None:
    command_bus, _ = compose()

    await command_bus.dispatch(
        OpenAccountCommand(
            account_id="acc-1", owner_id="user-1", initial_balance=100.0, currency="EUR"
        )
    )
    result = await command_bus.dispatch(
        DepositMoneyCommand(account_id="acc-1", amount=50.0, currency="EUR")
    )

    assert result.is_ok


async def test_compose_withdraw_money() -> None:
    command_bus, _ = compose()

    await command_bus.dispatch(
        OpenAccountCommand(
            account_id="acc-1", owner_id="user-1", initial_balance=200.0, currency="EUR"
        )
    )
    result = await command_bus.dispatch(
        WithdrawMoneyCommand(account_id="acc-1", amount=80.0, currency="EUR")
    )

    assert result.is_ok
