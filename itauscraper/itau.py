import click
import pickle
from services import itau_service
from helpers.formatter_helper import format_money_brl
from services.itau_service import SessionExpiredException
from models.bank_model import BankAccount
from models.auth_model import AuthCredentials

@click.group()
def commands():
    """Scraper para obter informações de contas (pessoa física) no banco Itaú"""
    pass

def __account_file(file_path: str = None) -> str:
    """Returns the file name for the account file"""
    file_name = f'bank_account.pkl'
    if file_path:
        return f'{file_path}/{file_name}'
    return file_name

def __credentials_file(file_path: str = None) -> str:
    """Returns the file name for the credentials file"""
    file_name = 'credentials.pkl'
    if file_path:
        return f'{file_path}/{file_name}'
    return file_name

def save_credentials(bank_account: BankAccount, credentials: AuthCredentials, file_path=None) -> None:
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

def load_saved_credentials(file_path=None) -> None:
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

# credentials that will be loaded from the file ( if exists )
bank_account: BankAccount = None
credentials: AuthCredentials = None 
load_saved_credentials() 

@click.command()
@click.argument('agencia', type=click.STRING, required=True)
@click.argument('conta', type=click.STRING, required=True)
@click.argument('senha', type=click.INT, required=True)
def login(agencia: str, conta: str, senha: int) -> None:
    """Inicia a conexão com o banco Itaú"""
    senha = str(senha)
    if len(senha) != 6:
        print('A senha deve conter apenas 6 "números"')
        exit(1)
    account = BankAccount(agencia, conta, senha)
    credentials = itau_service.generate_credentials(agencia, conta, senha)
    print(credentials)
    save_credentials(account, credentials)
    print("Login realizado com sucesso!")

@click.command()
def atualizar_credenciais() -> None:
    """Atualiza credenciais com conta, agência e senhas do ultimo login"""
    credentials = itau_service.generate_credentials(bank_account.agency, bank_account.account, bank_account.password)
    save_credentials(bank_account, credentials)

@click.command()
def extrato() -> None:
    """Extrato com transações dos últimos 90 dias"""
    __validate_credentials()
    extrato = None
    try:
        extrato = itau_service.account_statement(credentials)
    except SessionExpiredException:
        session_expired()

    print(f'{len(extrato.transactions)} transações nos útimos 90 dias na conta {bank_account.account} com {bank_account.agency}')
    print('## Data - Tipo - Valor - Descrição ##')
    for transaction in extrato.transactions:
        print(f'{transaction.date} - {transaction.type} - {format_money_brl(transaction.value)} - {transaction.description}')

@click.command()
def saldo() -> None:
    """Saldo disponível em conta"""
    __validate_credentials()
    balance = None
    try:
        balance = itau_service.account_balance(credentials)
    except SessionExpiredException:
        session_expired()
    print(f'Saldo disponível: {format_money_brl(balance)} na conta {bank_account.account} com agência {bank_account.agency}')
    
@click.command()
def cartoes() -> None:
    """Lista os cartões de crédito com suas faturas abertas"""
    __validate_credentials()
    cards = None
    try:
        cards = itau_service.list_credit_cards(credentials)
    except SessionExpiredException:
        session_expired()

    print('## Vencimento - Últimos dígitos - Nome - Valor da fatura ##')
    print(f'{len(cards)} cartões de crédito com faturas abertas')
    for credit_card in cards:
        invoice = credit_card.open_invoice
        print(f'{invoice.due_date} - {credit_card.last_digits} - {credit_card.name} - {format_money_brl(invoice.total)}')

@click.command()
def investimentos() -> None:
    """Saldo investido consolidado por categoria"""
    __validate_credentials()
    investments = None
    try:
        investments = itau_service.investiments(credentials)
    except:
        session_expired()

    print('## Ticker - Valor - Nome ##')
    for investment in investments:
        print(f'{investment.percentage}%  - {investment.category} - {format_money_brl(investment.amount)}')

@click.command()
def fiis() -> None:
    """Saldo (de cada ativo) investido em fundos imobiliários"""
    __validate_credentials()
    fiis = None
    try:
        fiis = itau_service.fiis(credentials)
    except:
        session_expired()

    print('## Percentual - Categoria - Valor ##')
    for fii in fiis:
        print(f'{fii.code} - {format_money_brl(fii.amount)} - {fii.name}')

def __validate_credentials():
    global bank_account, credentials
    if credentials is None and bank_account is None:
        print('Dados da conta bancária não encontrados, é necessário realizar o login')
        exit(1)
    if credentials is None:
        login(bank_account.agency, bank_account.account, bank_account.password)

def session_expired():
    print('Sessão expirada, é necessário "atualizar-credenciais" ou realizar o "login" novamente')
    exit(1)

# Add each function as a command option for the CLI
commands.add_command(login)
commands.add_command(saldo)
commands.add_command(extrato)
commands.add_command(cartoes)
commands.add_command(fiis)
commands.add_command(investimentos)
commands.add_command(atualizar_credenciais)

if __name__ == '__main__':
    commands()