import uuid
import requests
from requests import Response
from models.auth_model import AuthCredentials, Operation

from playwright.sync_api import sync_playwright
from playwright.sync_api._generated import Request as PWRequest
from playwright.sync_api._generated import Response as PWResponse


class ItauScraper:
    ITAU_URL = 'https://www.itau.com.br'
    INVESTMENT_URL = 'apicd.cloud.itau.com.br'
    LIST_CREDIT_CARDS_BODY = 'secao=Cartoes&item=Home'
    ACCOUNT_STATEMENT_BODY = 'filtro=periodoVisualizacao&valor=90'

    def __init__(self):
        self.user_agent = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/109.0.0.0 Safari/537.36'

    def account_statement(self, credentials: AuthCredentials) -> Response:
        """Get the account statement for the last 90 days"""
        headers = self.__headers(credentials, credentials.operationCodes.account_statement)
        headers['Content-Type'] = 'application/x-www-form-urlencoded'
        return requests.post(credentials.itau_router_url, headers=headers, data=self.ACCOUNT_STATEMENT_BODY)

    def credit_cards_list(self, credentials: AuthCredentials) -> Response:
        headers = self.__headers(credentials, credentials.operationCodes.cards_list)
        headers['Content-Type'] = 'application/x-www-form-urlencoded'
        return requests.post(credentials.itau_router_url, headers=headers, data=self.LIST_CREDIT_CARDS_BODY)

    def credit_card_details(self, credentials: AuthCredentials, ids: list[str]) -> Response:
        """
        Get the list of all credit cards with the open balance and general information.
        does NOT include the transactions for each card.
        """
        headers = self.__headers(credentials, credentials.operationCodes.cards_consolidated_statement)
        return requests.post(credentials.itau_router_url, headers=headers, json=ids)


    def investiment_details(self, credentials: AuthCredentials) -> Response:
        """
        Get the list of investiments by category and the total value of all
        does NOT individual investiments.
        """
        pass

    def is_session_expired(self, response: requests.Response) -> bool:
        return response.status_code != requests.status_codes.codes.OK

    def authentication(self, agency: str, account: str, password: str) -> AuthCredentials:
        """
        Fetch the authentication credential from Itaú bank website using playwright.
        the credentials are used to make requests to the bank API.
        """
        router_url: str = None
        x_client_id: str = None
        x_auth_token: str = None
        authorization: str = None
        cards_list_operation: str = None
        cards_details_operation: str = None
        account_statement_operation: str = None

        with sync_playwright() as pw:
            browser = pw.chromium.launch(
                headless=True,
                slow_mo=220,
            )

            context = browser.new_context(user_agent=self.user_agent)

            print(f'starting connection with {self.ITAU_URL}')
            page = context.new_page()

            def response_callback(response: PWResponse):
                nonlocal x_client_id, x_auth_token, authorization
                if 'router-app/router' not in response.url and self.INVESTMENT_URL not in response.url:
                    return

                if 'x-client-id' in response.headers:
                    x_client_id = response.headers['x-client-id']
                if 'x-auth-token' in response.headers:
                    x_auth_token = response.headers['x-auth-token']
                if 'authorization' in response.headers:
                    authorization = response.headers['authorization']

            def request_callback(request: PWRequest):
                nonlocal cards_list_operation, account_statement_operation, cards_details_operation, router_url
                if 'router-app/router' not in request.url and self.INVESTMENT_URL not in request.url:
                    return
                
                if 'router-app/router' in request.url:
                    router_url = request.url

                if request.post_data is None:
                    return
                
                if self.ACCOUNT_STATEMENT_BODY in request.post_data:
                    account_statement_operation = request.headers['op']
                if self.LIST_CREDIT_CARDS_BODY in request.post_data:
                    cards_list_operation = request.headers['op']
                if '[' in request.post_data and ']' in request.post_data:
                    cards_details_operation = request.headers['op']

            page.on("response", response_callback)
            page.on("request", request_callback)

            self.__login(page, account, agency, password)
            print(f'signed-in in the bank account {account} with agency {agency}')
                        
            self.__goto_account_statement(page)
            print(f'navigated to statement page for account {account} with agency {agency}')

            self.__goto_initial_banking_page(page)
            print(f'navigated to home page for account {account} with agency {agency}')

            self.__get_credit_card_balances(page)
            print(f'navigated to credit card page for account {account} with agency {agency}')

            page.close()
            context.close()
            browser.close()
        
        return AuthCredentials(router_url, x_client_id, x_auth_token, authorization,
                               Operation(cards_list_operation,
                                         cards_details_operation,
                                         account_statement_operation)
                               )

    def __headers(self, credentials: AuthCredentials, operation: str = None):
        return {
            'Accept': 'application/json, text/javascript, */*; q=0.01',
            'Content-Type': 'application/json',
            'Pragma': 'no-cache',
            'Origin': credentials.itau_router_url.split('/')[0],
            'Referer': credentials.itau_router_url,
            'User-Agent': self.user_agent,
            'X-Client-Id': credentials.x_client_id,
            'X-Auth-Token': credentials.x_auth_token,
            'X-FLOW-ID': self.__random_guid(),
            'op': operation,
        }
    
    def __random_guid(self) -> str:
        return str(uuid.uuid4())

    def __login(self, page, conta, agencia, senha):
        page.goto(self.ITAU_URL)

        print(f'filling account information for account {conta} with agency {agencia}')
        self.__fill_account_data(page, conta, agencia)

        print(f'filling internet banking password for account {conta} with agency {agencia}')
        self.__fill_secure_password(page, senha)

    def __fill_account_data(self, page, conta, agencia):
        """fill the account and agency number in the bank website"""
        page.click('#open_modal')
        page.wait_for_load_state('networkidle')

        page.click('#ag')  # click in the input with id = 'agencia'
        page.type('#ag', agencia, delay=50)

        page.click('#cc')
        page.type('#cc', conta, delay=50)

        page.wait_for_load_state('networkidle')
        page.click('#btn_acessos')
        page.wait_for_selector('#acessar')

    def __fill_secure_password(self, page, password):
        """
        fills the password to login in the account using the secure keyboard 
        provided in the bank website
        """
        keys = self.__get_number_keys(page)
        for digit in password:
            keys[digit].click()
            page.wait_for_timeout(1000)
        page.click('#acessar')
        page.wait_for_selector('#cartao-card-accordion')

    def __get_number_keys(self, page) -> dict:
        """ 
        Helper function that returns a dictionary with the number keys of the password keyboard.
        the keys are the numbers and the values are the elements in the page.
        note: this is the keyboard used to type passwords in a secure way inside the bank website
        """
        links = page.query_selector_all('.teclas.clearfix a')
        keys = {}
        for link in links:
            numbers = link.get_attribute('aria-label')
            # parse numbers from aria-label in the format "1 ou 3" and "2 ou 4"
            keys[numbers.split(' ')[0]] = link
            keys[numbers.split(' ')[2]] = link
        return keys

    def __get_credit_card_balances(self, page):
        """
        once logged in and in the account page,
        this function will navigate to the credit card balances page
        """
        page.click('#cartao-card-accordion')

        # wait for button with aria-label = 'mais cartões'
        mais_cartoes = 'button[aria-label="mais cartões"]'
        page.wait_for_selector(mais_cartoes)
        page.click(mais_cartoes)

        # wait for button with content = 'exibir mais cartões'
        exibir_mais_cartoes = 'button:has-text("exibir mais cartões")'
        page.wait_for_selector(exibir_mais_cartoes)
        page.click(exibir_mais_cartoes)
        page.wait_for_load_state('networkidle')

    def __goto_initial_banking_page(self, page):
        """Go to the initial banking page"""
        home = '#HomeLogo'
        page.wait_for_selector(home)
        page.click(home)
        page.wait_for_load_state('networkidle')

    def __goto_account_statement(self, page):
        """Open account statement page"""
        show_button = '#saldo-extrato-card-accordion'
        ver_extrato = 'button[aria-label="ver extrato"]'
        
        if not page.is_visible(ver_extrato):
            page.wait_for_selector(show_button)
            page.click(show_button)
        
        page.wait_for_selector(ver_extrato)
        page.click(ver_extrato)
        page.wait_for_load_state('networkidle')

        statement_select = '#extrato-filtro-lancamentos select'
        statement_days = "90"
        
        page.wait_for_selector(statement_select)
        page.select_option(statement_select, statement_days)
        page.wait_for_load_state('networkidle')
        page.wait_for_selector(statement_select)