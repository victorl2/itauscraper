import os
import pickle
import requests
from typing import Tuple
from services.itau_scraper_service import ItauScraper
from models.auth_model import AuthCredentials, Operation
from models.bank_model import CreditCard, OpenCreditCardInvoice
from helpers.formatter_helper import format_account_credentials

itau_scrapper = ItauScraper()

def generate_credentials(agency: str, account: str, password: str) -> AuthCredentials:
    return itau_scrapper.authentication(
        format_account_credentials(agency),
        format_account_credentials(account),
        password
    )

def save_credentials(agency: str, account: str, credentials: AuthCredentials, file_path=None) -> None:
    credentials_file = __credentials_file(agency, account, file_path)
    with open(credentials_file, 'wb') as file:
        pickle.dump(credentials, file, pickle.HIGHEST_PROTOCOL)

def load_saved_credentials(agency: str, account: str, file_path=None) -> AuthCredentials:
    credentials_file = __credentials_file(agency, account, file_path)
    if not os.path.exists(credentials_file):
        return None
    try:
        with open(credentials_file, 'rb') as file:
            return pickle.load(file)
    except:
        return None

def list_credit_cards(credentials: AuthCredentials) -> Tuple[list[CreditCard], Exception]:
    response_cards_list = itau_scrapper.credit_cards_list(credentials)
    if response_cards_list.status_code != requests.codes.ok:
        return None

    credit_card_ids = [card['id']
                       for card in response_cards_list.json()['object']['data']]
    response_cards_statement = itau_scrapper.credit_card_details(
        credentials, credit_card_ids)

    if response_cards_statement.status_code != requests.codes.ok:
        return None

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
            credit_card.total_limit = limites['limiteCreditoValor'],
            credit_card.used_limit = limites['limiteCreditoUtilizadoValor'],
            credit_card.available_limit = limites['limiteCreditoDisponivelValor'],

        faturas = card['faturas']
        if faturas is not None and len(faturas) > 0:
            faturas_abertas = [
                fatura for fatura in faturas if fatura['status'] == 'aberta']
            if len(faturas_abertas) == 0:
                continue

            credit_card.open_invoice = OpenCreditCardInvoice(
                total=faturas_abertas[0]['valorAberto'],
                due_date=faturas_abertas[0]['dataVencimento'],
                close_date=faturas_abertas[0]['dataFechamentoFatura']
            )

        credit_cards.append(credit_card)
    return credit_cards

def __credentials_file(agency: str, account: str, file_path: str) -> str:
    file_name = f'{format_account_credentials(agency)}_{format_account_credentials(account)}_credentials.pkl'
    if file_path:
        return f'{file_path}/{file_name}'
    return file_name