from dataclasses import dataclass, replace
from typing import Any, Self, cast

from seedwork.domain.domain_error import DomainError


class NullEntityIdError(DomainError):
    def __init__(self) -> None:
        super().__init__("Entity id cannot be None", "NULL_ENTITY_ID")


@dataclass(frozen=True, eq=False, kw_only=True)
class Entity[TId]:
    id: TId

    def __post_init__(self) -> None:
        if self.id is None:
            raise NullEntityIdError()

    def _evolve(self, **changes: Any) -> Self:
        return replace(self, **changes)

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Entity):
            return False
        if self is other:
            return True
        other_entity = cast(Entity[Any], other)
        if type(self) is not type(other_entity):
            return False
        return bool(self.id == other_entity.id)

    def __hash__(self) -> int:
        return hash(self.id)
