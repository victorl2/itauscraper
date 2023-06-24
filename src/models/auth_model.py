from dataclasses import dataclass

@dataclass
class AuthCredentials:
    x_client_id: str = None
    x_auth_token: str = None
    authorization: str = None