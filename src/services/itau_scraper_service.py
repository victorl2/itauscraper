import uuid
import requests

from enum import Enum
from fake_useragent import UserAgent 
import helpers.formatter_helper as formatter_helper
from models.auth_model import AuthCredentials

from playwright.sync_api import sync_playwright
from playwright.sync_api._generated import Request as PWRequest

class Operation(Enum):
    LIST_CARDS = 'aU/5fwTAn+SYQx5Y0ShO4SYxELMUNXeyBSEevDMzZbc=;'
    DETAIL_CARDS = 'mO9tDDVQSBxuoG8ovCgxjnjG3qd9BIWFvP4f85lnB6U=;'
    ACCOUNT_STATEMENT = 'ttH0rP/gIQU8RcKsbT+ibcQnmEIMpnyoUJOQBQ1UhAY=;'

class ItauScraper:
    RETRIES = 3
    ITAU_URL = 'https://www.itau.com.br'
    ROUTER_URL = 'https://internetpf6.itau.com.br/router-app/router'
    INVESTMENT_URL = f'https://apicd.cloud.itau.com.br/charon/orng2'

    ORIGIN = 'https://internetpf6.itau.com.br'
    REFERER = ROUTER_URL

    def __init__(self, agency: str, account: str, password: str):
        self.agency = formatter_helper.format_account_credentials(agency)
        self.account = formatter_helper.format_account_credentials(account)
        self.password = password
        
        self.x_client_id: str = None
        self.x_auth_token: str = None
        self.authorization: str = None
        self.last_update: str = None

        self.user_agent_generator = UserAgent(browsers=['edge', 'chrome', 'firefox', 'safari'])
        print(f'Scraper initialized for Itaú on agency {self.agency} and account {self.account}')

    def account_statement(self):
        """Get the account statement for the last 90 days"""
        response = self.__router_request(Operation.ACCOUNT_STATEMENT.value)
        return None

    def credit_card_details(self):
        """
        Get the list of all credit cards with the open balance and general information.
        does NOT include the transactions for each card.
        """
        list_response = self.__router_request(Operation.LIST_CARDS.value)
        if list_response.status_code == requests.status_codes.codes.OK:
            credit_card_ids = []
            details_response = self.__router_request(Operation.DETAIL_CARDS.value)
        return None

    def investiment_details(self):
        """
        Get the list of investiments by category and the total value of all
        does NOT individual investiments.
        """
        pass

    def __update_credentials(self, authorization: AuthCredentials):
        self.x_client_id = authorization.x_client_id
        self.x_auth_token = authorization.x_auth_token
        self.authorization = authorization.authorization

    def __router_request(self, operation: str, data: dict = None, tries: int = 0) -> requests.Response:
        if tries >= self.RETRIES:
            return requests.Response(status=503, text='Max retries reached')
        
        response = requests.post(self.ROUTER_URL, headers=self.__headers(operation), data=data)
        if self.__is_session_expired(response):
            credentials = self.__authentication()
            self.__update_credentials(credentials)
            return self.__router_request(operation, data, tries + 1)
        return response
        
    def __headers(self, operation: str, extras: dict = []):
        return {
            'Accept': 'application/json, text/javascript, */*; q=0.01',
            'Content-Type': 'application/x-www-form-urlencoded',
            'Pragma': 'no-cache',
            'Origin': self.ORIGIN,
            'Referer': self.REFERER,
            'User-Agent': self.__random_user_agent(),
            'X-Client-Id': self.x_client_id,
            'X-Auth-Token': self.x_auth_token,
            'X-FLOW-ID': self.__random_guid(),
            'op': operation
        }.update(extras)
    
    
    def __is_session_expired(self, response: requests.Response) -> bool:
        return response.status_code != requests.status_codes.codes.OK

    def __random_user_agent(self) -> str:
        return self.user_agent_generator.random

    def __random_guid(self) -> str:
        return str(uuid.uuid4())
    
    def __login(self, page, conta, agencia, senha):
        page.goto('https://www.itau.com.br')
        self.__fill_account_data(page, conta, agencia)
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
        keys =  self.__get_number_keys(page)
        for digit in password:
             keys[digit].click()
             page.wait_for_timeout(1000)
        page.click('#acessar')
        page.wait_for_selector('#cartao-card-accordion')
        
    def __get_number_keys(self, page) -> dict:
        """ 
        Helper functions that returns a dictionary with the number keys of the password keyboard.
        the keys are the numbers and the values are the elements in the page.
        note: this is the keyboard used to type passwords in a secure way inside the bank website
        """
        links =  page.query_selector_all('.teclas.clearfix a')
        keys = {}
        for link in links:
            numbers =  link.get_attribute('aria-label')
            # parse numbers from aria-label in the format "1 ou 3" and "2 ou 4"
            keys[numbers.split(' ')[0]] = link
            keys[numbers.split(' ')[2]] = link
        return keys
    
    def __authentication(self) -> AuthCredentials:
        """
        Fetch the authentication credential from Itaú bank website using playwright.
        the credentials are used to make requests to the bank API.
        """
        with sync_playwright() as pw:
            browser = pw.chromium.launch(
                headless=True,
                slow_mo=220,
            )

            context = browser.new_context(
                user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/109.0.0.0 Safari/537.36',
            )

            print(f'starting connection with itau.com.br')
            page = context.new_page()

            x_client_id: str = None
            x_auth_token: str = None
            authorization: str = None
            
            def request_callback(request: PWRequest):
                global x_client_id, x_auth_token, authorization
                if 'router-app/router' not in request.url and 'apicd.cloud.itau.com.br' not in request.url:
                    return
                if 'x-client-id' in request.headers:
                    x_client_id = request.headers['x-client-id']
                if 'x-auth-token' in request.headers:
                    x_auth_token = request.headers['x-auth-token']
                if 'Authorization' in request.headers:
                    authorization = request.headers['Authorization']

            page.on("request", request_callback)
            print(f'signed-in in the bank account {self.account} with agency {self.agency}')
            self.__login(page, self.account, self.agency, self.password)

            page.close()
            context.close()
            browser.close()
        return AuthCredentials(x_client_id, x_auth_token, authorization)