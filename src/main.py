import os
import dotenv
from models.auth_model import AuthCredentials
from services.itau_scraper_service import ItauScraper
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
    
    itau_scrapper = ItauScraper()
    authToken = itau_scrapper.authentication(agency, account, password)
    print(f'credentials generated for {agency}/{account}')