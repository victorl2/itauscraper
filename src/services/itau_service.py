import os
import pickle
from models.auth_model import AuthCredentials, Operation
from models.bank_model import CreditCard, OpenCreditCardInvoice
from services.itau_scraper_service import ItauScraper

itau_scrapper = ItauScraper()

def generate_credentials(agency: str, account: str, password: str) -> AuthCredentials:
    return itau_scrapper.authentication(agency, account, password)

def save_credentials(agency:str, account: str, credentials: AuthCredentials) -> None:
    credentialsFile = f'{agency}_{account}_credentials.pkl'
    with open(credentialsFile, 'wb') as file:
        pickle.dump(credentials, file, pickle.HIGHEST_PROTOCOL)

def load_saved_credentials(agency:str, account: str) -> AuthCredentials:
    credentialsFile = f'{agency}_{account}_credentials.pkl'
    if not os.path.exists(credentialsFile):
        return None
    try:
        with open(credentialsFile, 'rb') as file:
            return pickle.load(file)
    except:
        return None

def list_credit_cards(credentials: AuthCredentials) -> list[CreditCard]:
    response_cards_list = itau_scrapper.credit_cards_list(credentials)
    credit_card_ids = [card['id'] for card in response_cards_list.json()['object']['data']]

    response_cards_statement = itau_scrapper.credit_card_details(credentials, credit_card_ids)
    credit_cards: list[CreditCard] = []
    for card in response_cards_statement.json()['object']:
        credit_card = CreditCard(
            id=card['id'],
            name=card['nome'],
            last_digits=card['numero'],
            expiration_date=card['vencimento'],
        )

        limites = card['limites']
        if limites is not None and len(limites) > 0:
            credit_card.total_limit=limites['limiteCreditoValor'],
            credit_card.used_limit=limites['limiteCreditoUtilizadoValor'],
            credit_card.available_limit=limites['limiteCreditoDisponivelValor'],
        
        faturas = card['faturas']
        if faturas is not None and len(faturas) > 0:
            faturas_abertas = [fatura for fatura in faturas if fatura['status'] == 'aberta']
            if len(faturas_abertas) == 0:
                continue
            
            credit_card.open_invoice=OpenCreditCardInvoice(
                total=faturas_abertas[0]['valorAberto'],
                due_date=faturas_abertas[0]['dataVencimento'],
                close_date=faturas_abertas[0]['dataFechamentoFatura']
            )

        credit_cards.append(credit_card)
    return credit_cards

