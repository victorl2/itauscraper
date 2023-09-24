import json
import requests
from helpers.formatter_helper import brl_str_to_float, format_to_brl_date
from models.auth_model import AuthCredentials
from models.bank_model import CreditCard, OpenCreditCardInvoice, AccountStatement, Statement, Investment, Asset

from services.itau_scraper_service import ItauScraper
from helpers.formatter_helper import format_account_credentials

itau_scrapper = ItauScraper()


def generate_credentials(agency: str, account: str, password: str) -> AuthCredentials:
    return itau_scrapper.authentication(
        format_account_credentials(agency),
        format_account_credentials(account),
        password
    )


def account_statement(credentials: AuthCredentials) -> AccountStatement:
    response = itau_scrapper.account_statement(credentials)
    __validate_session(response)

    if response.status_code != requests.codes.ok:
        return None

    response_body = response.json()
    invoice_statements = response_body['lancamentos']
    account_statements: list[Statement] = []
    for statement in invoice_statements:
        date = statement['dataLancamento']
        amount = statement['valorLancamento']
        description = statement['descricaoLancamento']
        incoming_amount = statement['ePositivo']

        skip_description = ['SDO CTA/APL AUTOMATICAS', 'SALDO DO DIA']
        if date is None or amount is None or description in skip_description:
            continue
        
        account_statements.append(
            Statement(
                date=date,
                description=description if description is not None else '###',
                value=brl_str_to_float(amount),
                type='entrada' if incoming_amount else 'saida'
            )
        )

    balance = response_body['saldoResumido']["saldoContaCorrente"]["valor"]
    return AccountStatement(
        available_balance=float(balance.replace('.', '').replace(',', '.')),
        transactions=account_statements
    )


def account_balance(credentials: AuthCredentials) -> float:
    statement = account_statement(credentials)
    if statement is None:
        return None
    return statement.available_balance

def fiis(credentials: AuthCredentials) -> list[Asset]:
    investments = __generate_json_investments(credentials)
    fiis: list[Asset] = []

    category_fii = "investimentosimobiliarios"

    for investment in investments:
        if investment["tipoOrdenado"] != category_fii:
            continue

        fiis.extend([Asset(
                        code=asset['codigoProduto'] if 'codigoProduto' in asset else 'Unknown',
                        name=asset['nomeProduto'] if 'nomeProduto' in asset else 'Unknown',
                        amount=asset['valorInvestidoGrafico'] if 'valorInvestidoGrafico' in asset else 0.0,
                    ) for asset in investment['subLista']])
    fiis.sort(key=lambda x: x.amount, reverse=True)
    return fiis

def investiments(credentials: AuthCredentials) -> list[Investment]:
    """all consolidated investiments """
    investments = __generate_json_investments(credentials)
    investiments_list: list[Investment] = []

    for investment in investments:
        investiments_list.append(
            Investment(
                category=investment["subLista"][0]["tipoInvestimento"] if 'tipoInvestimento' in investment["subLista"][0] else 'Unknown',
                amount=investment['valorParaGrafico'] if 'valorParaGrafico' in investment else 0.0,
                percentage=investment['percentualTotal'] if 'percentualTotal' in investment else 0.0,
                assets=[
                    Asset(
                        code=asset['codigoProduto'] if 'codigoProduto' in asset else 'Unknown',
                        name=asset['nomeProduto'] if 'nomeProduto' in asset else 'Unknown',
                        amount=asset['valorInvestidoGrafico'] if 'valorInvestidoGrafico' in asset else 0.0,
                    ) for asset in investment['subLista']
                ]
            )
        )
    return investiments_list


def list_credit_cards(credentials: AuthCredentials) -> list[CreditCard]:
    response_cards_list = itau_scrapper.credit_cards_list(credentials)
    __validate_session(response_cards_list)
    if response_cards_list.status_code != requests.codes.ok:
        return None
    
    response_cards_statement = itau_scrapper.credit_card_details(
        credentials=credentials,
        ids=[card['id']
             for card in response_cards_list.json()['object']['data']]
    )

    __validate_session(response_cards_statement)
    if response_cards_statement.status_code != requests.codes.ok:
        return None

    credit_cards: list[CreditCard] = []
    for card in response_cards_statement.json()['object']:
        credit_card = CreditCard(
            id=card['id'],
            name=card['nome'],
            last_digits=card['numero'],
            expiration_date=format_to_brl_date(card['vencimento']),
        )

        limites = card['limites']
        if limites is not None and len(limites) > 0:
            credit_card.total_limit = brl_str_to_float(limites['limiteCreditoValor']),
            credit_card.used_limit = brl_str_to_float(limites['limiteCreditoUtilizadoValor']),
            credit_card.available_limit = brl_str_to_float(limites['limiteCreditoDisponivelValor']),

        invoices = card['faturas']
        if invoices is not None and len(invoices) > 0:
            open_invoices = [
                invoice for invoice in invoices if invoice['status'] == 'aberta']
            closed_invoices = [ 
                invoice for invoice in invoices if invoice['status'] == 'fechada']
            
            if len(open_invoices) == 0 and len(closed_invoices) == 0:
                continue

            credit_card.open_invoice = OpenCreditCardInvoice(
                total=brl_str_to_float(open_invoices[0]['valorAberto']) if len(open_invoices) > 0 else brl_str_to_float(closed_invoices[0]['valorAberto']),
                due_date=format_to_brl_date(open_invoices[0]['dataVencimento']) if len(open_invoices) > 0 else format_to_brl_date(closed_invoices[0]['dataVencimento']),
                close_date=format_to_brl_date(open_invoices[0]['dataFechamentoFatura']) if len(open_invoices) > 0 else format_to_brl_date(closed_invoices[0]['dataFechamentoFatura']) 
            )

        credit_cards.append(credit_card)
    return credit_cards


def __generate_json_investments(credentials: AuthCredentials):
    investiments = itau_scrapper.investiment_details(credentials)
    __validate_session(investiments)
    start_str = "jQuery.parseJSON('"
    start_index = investiments.text.index(start_str)
    end = investiments.text.index("]')", start_index)

    json_payload = investiments.text[start_index +
                                     len(start_str):end].strip() + ']'
    return json.loads(json_payload)

def __validate_session(response):
    if response.status_code != requests.codes.ok and 'foi encerrada por falta de' in response.text:
        raise SessionExpiredException(
            'Sessão finalizada, faça o login novamente')


# custom exception for when the session is expired
class SessionExpiredException(Exception):
    pass
