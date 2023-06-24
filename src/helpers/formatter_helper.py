EMPTY = ""

def format_account_credentials(account_credentials: str) -> str:
    return account_credentials.replace('-', EMPTY).replace('.', EMPTY).strip()