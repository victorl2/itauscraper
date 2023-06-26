from dataclasses import dataclass

@dataclass
class Operation:
    cards_list: str = None
    cards_consolidated_statement: str = None
    account_statement: str = None

@dataclass
class AuthCredentials:
    itau_router_url: str = None
    x_client_id: str = None
    x_auth_token: str = None
    authorization: str = None
    operationCodes: Operation = None