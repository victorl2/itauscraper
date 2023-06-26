from dataclasses import dataclass

@dataclass
class Statement:
    date: str = None
    description: str = None
    value: str = None
    balance: str = None

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