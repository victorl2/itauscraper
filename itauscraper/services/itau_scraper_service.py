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
    INVESTMENT_BODY = 'isAberto=false'

    def __init__(self):
        self.user_agent = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/109.0.0.0 Safari/537.36'

    def account_statement(self, credentials: AuthCredentials) -> Response:
        """Get the account statement for the last 90 days"""
        headers = self.__headers(
            credentials, credentials.operationCodes.account_statement)
        headers['Content-Type'] = 'application/x-www-form-urlencoded'
        return requests.post(credentials.itau_router_url, headers=headers, data=self.ACCOUNT_STATEMENT_BODY)

    def credit_cards_list(self, credentials: AuthCredentials) -> Response:
        headers = self.__headers(
            credentials, credentials.operationCodes.cards_list)
        headers['Content-Type'] = 'application/x-www-form-urlencoded'
        return requests.post(credentials.itau_router_url, headers=headers, data=self.LIST_CREDIT_CARDS_BODY)

    def credit_card_details(self, credentials: AuthCredentials, ids: list[str]) -> Response:
        """
        Get the list of all credit cards with the open balance and general information.
        does NOT include the transactions for each card.
        """
        headers = self.__headers(
            credentials, credentials.operationCodes.cards_consolidated_statement)
        return requests.post(credentials.itau_router_url, headers=headers, json=ids)

    def investiment_details(self, credentials: AuthCredentials) -> Response:
        """
        Get the list of investiments by category and the total value of all
        does NOT individual investiments.
        """
        headers = self.__headers(
            credentials, credentials.operationCodes.investments)
        headers['Content-Type'] = 'application/x-www-form-urlencoded'
        return requests.post(credentials.itau_router_url, headers=headers, data=self.INVESTMENT_BODY)

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
        cards_list_operation: str = None
        cards_details_operation: str = None
        account_statement_operation: str = None
        investment_operation: str = None

        with sync_playwright() as pw:
            browser = pw.chromium.launch(
                headless=False,
                slow_mo=220,
            )

            context = browser.new_context(user_agent=self.user_agent)

            print(f'starting connection with {self.ITAU_URL}')
            page = context.new_page()

            def response_callback(response: PWResponse):
                nonlocal x_client_id, x_auth_token, investment_operation
                if 'router-app/router' not in response.url and self.INVESTMENT_URL not in response.url:
                    return
                
                if response.request.headers == None or len(response.request.headers) == 0:
                    raise Exception('request headers are empty')

                if 'x-client-id' in response.headers:
                    x_client_id = response.headers['x-client-id']
                if 'x-auth-token' in response.headers:
                    x_auth_token = response.headers['x-auth-token']
                try:
                    body_text = response.text()
                    if body_text is not None and "ordenadoPorTipo" in body_text:
                        investment_operation = response.request.headers['op']           
                except:
                    pass

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

            account_description = f'account {account} with agency {agency}'

            self.__login(page, account, agency, password)
            print(f'signed-in in the bank account {account_description}')

            self.__goto_investments(page)
            print(f'open investment option for {account_description}')

            self.__goto_initial_banking_page(page)
            print(f'navigated to home page for {account_description}')

            self.__goto_account_statement(page)
            print(f'navigated to statement page for {account_description}')

            self.__goto_initial_banking_page(page)
            print(f'navigated to home page for {account_description}')

            self.__get_credit_card_balances(page)
            print(f'navigated to credit card page for {account_description}')

            page.close()
            context.close()
            browser.close()

        return AuthCredentials(router_url, x_client_id, x_auth_token,
                               Operation(cards_list_operation,
                                         cards_details_operation,
                                         account_statement_operation,
                                         investment_operation)
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

        print(
            f'filling account information for account {conta} with agency {agencia}')
        self.__fill_account_data(page, conta, agencia)

        itoken = input("enter your itau itoken:")  
        self.__fill_itoken(page, itoken.strip())

        print(
            f'filling internet banking password for account {conta} with agency {agencia}')
        self.__fill_secure_password(page, senha)

    def __fill_account_data(self, page, conta, agencia):
        """fill the account and agency number in the bank website"""
        page.click('button#open_modal_more_access')
        page.wait_for_selector('div.idl-modal-more-access-container')

        page.click('input#idl-more-access-input-agency')  # click in the input with id = 'agencia'

        print("typing agency")
        page.type('input#idl-more-access-input-agency', agencia, delay=50)

        page.click('input#idl-more-access-input-account')

        print("typing account")
        page.type('input#idl-more-access-input-account', conta, delay=50)

        # accept cookies
        if page.locator("button#itau-cookie-consent-banner-accept-cookies-btn").is_visible():
            page.click("button#itau-cookie-consent-banner-accept-cookies-btn")

        page.wait_for_selector('button#idl-more-access-submit-button:not([disabled])')
        page.click('button#idl-more-access-submit-button')
        page.wait_for_load_state('networkidle')


    def __fill_itoken(self, page, itoken):
        """
        fill the required itoken
        """
        page.wait_for_selector('input#app-entraCodigo')
        page.click('input#app-entraCodigo')
        print("typing itoken")
        page.type('input#app-entraCodigo', itoken, delay=50)
        page.wait_for_selector('a#app-codigoOk:not([disabled])')
        page.click('a#app-codigoOk')
        page.wait_for_load_state('networkidle')
        


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
        page.wait_for_selector('.teclas.clearfix a')
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
        expandir_cartoes = 'button#cartao-card-accordion'
        cartoes_table = 'div.content-cartoes'
        while not page.locator(cartoes_table).is_visible():
            page.wait_for_selector(expandir_cartoes)
            page.click(expandir_cartoes)
            page.wait_for_timeout(2000)
            

    def __goto_initial_banking_page(self, page):
        """Go to the initial banking page"""
        home = '#HomeLogo'
        page.wait_for_selector(home)
        page.click(home)

    def __goto_investments(self, page):
        """Open the investment options on the bank account home page"""
        show_investments = "#investimento-card-accordion"
        page.wait_for_selector(show_investments)
        page.click(show_investments)

        open_investments = "#verInvestimentos"
        page.wait_for_selector(open_investments)
        page.click(open_investments)

    def __goto_account_statement(self, page):
        """Open account statement page"""
        show_button = '#saldo-extrato-card-accordion'
        ver_extrato = 'button[aria-label="ver extrato"]'

        if not page.is_visible(ver_extrato):
            page.wait_for_selector(show_button)
            page.click(show_button)

        page.wait_for_load_state('domcontentloaded')
        page.wait_for_selector(ver_extrato)
        
        page.click(ver_extrato)
        page.wait_for_load_state('domcontentloaded')

        statement_select = 'div#periodoFiltro'
        statement_days = "90"

        page.click(statement_select)  # Replace with the selector for the expandable div

        page.wait_for_selector("ul#periodoFiltroList")
        # Scroll to the last item in the list to ensure all options are loaded
        list_items = page.locator("ul#periodoFiltroList li")  # Select all list items; adjust the selector if necessary

        # Scroll until you find the specific 'li' with `data-id="90"`
        for i in range(list_items.count()):
            item = list_items.nth(i)
            item.scroll_into_view_if_needed()
            
            # Check if the item has `data-id="90"`
            if item.get_attribute("data-id") == statement_days:
                item.click()
                break
        page.wait_for_load_state('networkidle')
