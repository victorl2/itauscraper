import os
import dotenv
from services.itau_scraper_service import ItauScraper

if __name__ == '__main__':
    dotenv.load_dotenv()
    agencia: str = os.getenv("AGENCY_NUMBER")
    conta: str = os.getenv("ACCOUNT_NUMBER")
    password: str = os.getenv("ACCOUNT_PASSWORD")

    if not agencia or agencia == '':
        raise ValueError('AGENCY_NUMBER environment variable is not set')
    
    if not conta or conta == '':
        raise ValueError('ACCOUNT_NUMBER environment variable is not set')
    
    if not password or password == '':
        raise ValueError('ACCOUNT_PASSWORD environment variable is not set')

    itau_scrapper = ItauScraper(agency=agencia, 
                                account=conta, 
                                password=password)

    itau_scrapper.account_statement()
