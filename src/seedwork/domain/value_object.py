from abc import ABC
from dataclasses import dataclass


# B024/B027: ValueObject is intentionally abstract without @abstractmethod.
# validate() is a no-op hook — subclasses with no invariants need not override it.
@dataclass(frozen=True, kw_only=True)
class ValueObject(ABC):  # noqa: B024
    def __post_init__(self) -> None:
        self.validate()

    def validate(self) -> None:  # noqa: B027
        pass
