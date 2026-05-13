from bank_account.application.open_account.open_account_command import OpenAccountCommand
from bank_account.domain.bank_account import BankAccount
from bank_account.domain.bank_account_id import BankAccountId
from bank_account.domain.bank_account_repository import BankAccountRepository
from bank_account.domain.money import Money

from seedwork.application.commands import CommandHandler


class OpenAccountHandler(CommandHandler[OpenAccountCommand]):
    def __init__(self, repository: BankAccountRepository) -> None:
        self._repository = repository

    async def handle(self, command: OpenAccountCommand) -> None:
        account = BankAccount.open(
            id=BankAccountId(command.account_id),
            initial_balance=Money(amount=command.initial_balance, currency=command.currency),
        )
        await self._repository.save(account)
