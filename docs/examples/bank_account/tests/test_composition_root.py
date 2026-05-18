from bank_account.application.open_account.open_account_command import OpenAccountCommand
from bank_account.composition_root import compose

from seedwork.testing import InMemoryIntegrationEventPublisher


async def test_compose_open_account_publishes_integration_event() -> None:
    publisher = InMemoryIntegrationEventPublisher()
    command_bus, _ = compose(integration_publisher=publisher)

    await command_bus.dispatch(
        OpenAccountCommand(account_id="acc-1", initial_balance=100.0, currency="EUR")
    )

    assert len(publisher.published) == 1
    event = publisher.published[0]
    assert event.type == "bank_account.account_opened"
    assert event.aggregate_id == "acc-1"
    assert event.causation_id is not None
    assert event.payload["initial_balance"] == 100.0
    assert event.payload["currency"] == "EUR"
