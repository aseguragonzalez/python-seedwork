from dataclasses import dataclass
from datetime import UTC, datetime

from seedwork.domain.domain_event import BaseDomainEvent, DomainEvent


@dataclass(frozen=True, kw_only=True)
class OrderPlacedPayload:
    order_id: str
    total: float


@dataclass(frozen=True)
class OrderPlaced(BaseDomainEvent[OrderPlacedPayload]):
    pass


def _make_event() -> OrderPlaced:
    return OrderPlaced(
        aggregate_id="ord-1",
        payload=OrderPlacedPayload(order_id="ord-1", total=42.0),
    )


def test_domain_event_record_auto_generates_id() -> None:
    event = _make_event()
    assert isinstance(event.id, str)
    assert len(event.id) > 0


def test_domain_event_record_two_instances_have_different_ids() -> None:
    a = _make_event()
    b = _make_event()
    assert a.id != b.id


def test_domain_event_record_occurred_at_is_utc() -> None:
    event = _make_event()
    assert event.occurred_at.tzinfo is UTC


def test_domain_event_record_occurred_at_is_recent() -> None:
    before = datetime.now(UTC)
    event = _make_event()
    after = datetime.now(UTC)
    assert before <= event.occurred_at <= after


def test_domain_event_record_payload_is_preserved() -> None:
    event = _make_event()
    assert event.payload.order_id == "ord-1"
    assert event.payload.total == 42.0


def test_domain_event_record_satisfies_domain_event_protocol() -> None:
    event = _make_event()
    assert isinstance(event.id, str)
    assert isinstance(event.occurred_at, datetime)
    assert isinstance(event.aggregate_id, str)


def test_domain_event_protocol_is_structural() -> None:
    class MinimalEvent:
        @property
        def id(self) -> str:
            return "evt-id"

        @property
        def occurred_at(self) -> datetime:
            return datetime.now(UTC)

        @property
        def aggregate_id(self) -> str:
            return "agg-1"

    event: DomainEvent = MinimalEvent()
    assert event.id == "evt-id"
    assert event.aggregate_id == "agg-1"


def test_domain_event_record_is_immutable() -> None:
    from dataclasses import FrozenInstanceError

    import pytest

    event = _make_event()
    with pytest.raises(FrozenInstanceError):
        event.id = "tampered"  # type: ignore[misc]
