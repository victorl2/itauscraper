import os
import dotenv
from models.auth_model import AuthCredentials, Operation
from services import itau_service
from helpers.formatter_helper import format_account_credentials

if __name__ == '__main__':
    dotenv.load_dotenv()
    agency: str = os.getenv("AGENCY_NUMBER")
    account: str = os.getenv("ACCOUNT_NUMBER")
    password: str = os.getenv("ACCOUNT_PASSWORD")

    if not agency or agency == '':
        raise ValueError('AGENCY_NUMBER environment variable is not set')
    
    if not account or account == '':
        raise ValueError('ACCOUNT_NUMBER environment variable is not set')
    
    if not password or password == '':
        raise ValueError('ACCOUNT_PASSWORD environment variable is not set')

    agency = format_account_credentials(agency)
    account = format_account_credentials(account)
    
    credentials = itau_service.load_saved_credentials()
    if credentials is None:
        credentials = itau_service.generate_credentials(agency, account, password)
        itau_service.save_credentials(credentials)

    cards = itau_service.list_credit_cards(credentials)
    print('Credit cards:')
    print(cards)