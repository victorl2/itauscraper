import datetime

def format_account_credentials(account_credentials: str) -> str:
    return account_credentials.replace('-', "").replace('.', "").strip()

def format_money_brl(money) -> str:
    """Format money to BRL - add R$ and . as separator for thousands and , for decimals"""
    if money is None:
        return None
    value = float(money)
    return f'R$ {value:,.2f}'.replace(',', 'v').replace('.', ',').replace('v', '.')

def brl_str_to_float(money: str) -> float:
    """Converts a BRL string to float"""
    if money is None:
        return None
    return float(money.replace('R$', '').replace('.', '').replace(',', '.'))

def format_to_brl_date(date: str) -> str:
    """Format str from 2023-07-08 to 08/07/2023"""
    if date is None:
        return None
    return datetime.datetime.strptime(date, '%Y-%m-%d').strftime('%d/%m/%Y')