from bank_account.application.deposit_money.deposit_money_command import DepositMoneyCommand
from bank_account.domain.bank_account_id import BankAccountId
from bank_account.domain.bank_account_repository import BankAccountRepository
from bank_account.domain.errors import AccountNotFoundError
from bank_account.domain.money import Money

from seedwork.application.commands import CommandHandler


class DepositMoneyHandler(CommandHandler[DepositMoneyCommand]):
    def __init__(self, repository: BankAccountRepository) -> None:
        self._repository = repository

    async def handle(self, command: DepositMoneyCommand) -> None:
        account = await self._repository.find_by_id(BankAccountId(command.account_id))
        if account is None:
            raise AccountNotFoundError(command.account_id)
        updated = account.credit(Money(amount=command.amount, currency=command.currency))
        await self._repository.save(updated)
