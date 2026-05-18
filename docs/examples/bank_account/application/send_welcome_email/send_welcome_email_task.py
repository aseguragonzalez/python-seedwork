from __future__ import annotations

from typing import TYPE_CHECKING, ClassVar
from uuid import uuid4

from bank_account.application.request_context import correlation_id as _correlation_id

from seedwork.application.background_tasks import BaseBackgroundTask

if TYPE_CHECKING:
    from bank_account.domain.events.account_opened import AccountOpened


class SendWelcomeEmailTask(BaseBackgroundTask):
    TYPE: ClassVar[str] = "send_welcome_email"

    @classmethod
    def from_domain_event(cls, event: AccountOpened) -> SendWelcomeEmailTask:
        return cls(
            type=cls.TYPE,
            payload={"account_id": event.aggregate_id},
            correlation_id=_correlation_id.get(str(uuid4())),
            causation_id=event.id,
        )
