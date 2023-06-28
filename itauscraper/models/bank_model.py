from dataclasses import dataclass

@dataclass
class Statement:
    date: str = None
    description: str = None
    value: str = None

@dataclass
class BankAccount:
    agency: str = None
    account: str = None
    password: str = None

@dataclass
class AccountStatement:
    available_balance: str = None
    transactions: list[Statement] = None


@dataclass
class OpenCreditCardInvoice:
    total: str = None
    due_date: str = None
    close_date: str = None

@dataclass
class CreditCard:
    id: str = None
    name: str = None
    last_digits: str = None
    expiration_date: str = None
    total_limit: str = None
    used_limit: str = None
    available_limit: str = None
    open_invoice: OpenCreditCardInvoice = None

@dataclass
class Asset:
    code: str = None
    name: str = None
    amount: float = None

@dataclass
class Investment:
    category: str = None
    amount: float = None
    percentage: str = None
    assets: list[Asset] = None


