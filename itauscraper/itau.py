import click
import pickle
from services import itau_service
from models.bank_model import BankAccount
from models.auth_model import AuthCredentials

@click.group()
def commands():
    """Scraper para obter informações de contas (pessoa física) no banco Itaú"""
    pass

def __account_file(file_path: str = "data") -> str:
    """Returns the file name for the account file"""
    file_name = f'bank_account.pkl'
    if file_path:
        return f'{file_path}/{file_name}'
    return file_name

def __credentials_file(file_path: str = "data") -> str:
    """Returns the file name for the credentials file"""
    file_name = 'credentials.pkl'
    if file_path:
        return f'{file_path}/{file_name}'
    return file_name

def save_credentials(bank_account: BankAccount, credentials: AuthCredentials, file_path="data") -> None:
    """Saves the credentials and bank account to a file"""
    if bank_account is None:
        raise Exception('Bank account information needs to be avalilable')
    
    credentials_file = __credentials_file(file_path)
    account_file = __account_file(file_path)

    if credentials is not None:
        with open(credentials_file, 'wb') as file:
            pickle.dump(credentials, file, pickle.HIGHEST_PROTOCOL)
    
    with open(account_file, 'wb') as file:
        pickle.dump(bank_account, file, pickle.HIGHEST_PROTOCOL)

def load_saved_credentials(file_path="data") -> None:
    global bank_account, credentials

    credentials_file = __credentials_file(file_path)
    account_file = __account_file(file_path)

    try:
        with open(credentials_file, 'rb') as file:
            credentials = pickle.load(file)
        with open(account_file, 'rb') as file:
            bank_account = pickle.load(file)
    finally:
        return

bank_account: BankAccount = None
credentials: AuthCredentials = None 
load_saved_credentials()


@click.command()
@click.argument('agencia', type=click.STRING, required=True)
@click.argument('conta', type=click.STRING, required=True)
@click.argument('senha', type=click.INT, required=True)
def login(agencia: str, conta: str, senha: int) -> None:
    """Inicia a conexão conexão com o banco e Itau"""
    senha = str(senha)
    if len(senha) != 6:
        print('A senha deve conter apenas 6 "números"')
        exit(1)
    account = BankAccount(agencia, conta, senha)
    credentials = itau_service.generate_credentials(agencia, conta, senha)
    save_credentials(account, credentials)
    print("Login realizado com sucesso!")

@click.command()
def extrato() -> None:
    """Extrato com transações dos últimos 90 dias"""
    extrato = itau_service.account_statement(credentials)
    print(f'{len(extrato.transactions)} transações nos útimos 90 dias na conta {bank_account.account} e agência {bank_account.agency}')
    for transaction in extrato.transactions:
        print(f'{transaction.date} - R$ {transaction.value} - {transaction.description}')

@click.command()
def saldo() -> None:
    """Saldo disponível em conta"""
    balance = itau_service.account_balance(credentials)
    print(f'Saldo disponível: R$ {balance} na conta {bank_account.account} e agência {bank_account.agency}')
    
@click.command()
def cartoes() -> None:
    """Lista os cartões de crédito com suas faturas abertas"""
    itau_service.list_credit_cards(credentials)
    
commands.add_command(login)
commands.add_command(saldo)
commands.add_command(extrato)
commands.add_command(cartoes)

if __name__ == '__main__':
    commands()