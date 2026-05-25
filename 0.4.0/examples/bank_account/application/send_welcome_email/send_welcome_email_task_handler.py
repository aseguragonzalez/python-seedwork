from bank_account.application.send_welcome_email.send_welcome_email_task import SendWelcomeEmailTask

from seedwork.application.background_tasks import TaskHandler


class SendWelcomeEmailTaskHandler(TaskHandler[SendWelcomeEmailTask]):
    async def handle(self, task: SendWelcomeEmailTask) -> None:
        pass
