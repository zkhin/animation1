from ak_requests import RequestsSession
from bs4 import BeautifulSoup
import requests
from selenium.common import exceptions
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from functools import cached_property
import logging
import os
from typing import Literal

#Disable webdriver-manager logs per https://github.com/SergeyPirogov/webdriver_manager#wdm_log
os.environ['WDM_LOG'] = str(logging.NOTSET)

class Browser:
    MAX_WAIT_TIME: float = 10
    IMPLICITLY_WAIT_TIME: float = 3
    EXCEPTIONS = exceptions
    
    def __init__(self, driver) -> None:
        self.driver = driver

    def wait_for_locator(self, locator: tuple[str, str]) -> None:
        """
        Wait until the element with the specified locator is present.

        Args:
            locator (tuple): The locator tuple (By, value) of the element to wait for.
        """
        (
            WebDriverWait(self.driver, self.MAX_WAIT_TIME, 0.5)
            .until(EC.presence_of_element_located(locator))
        )
        return None
    
    @staticmethod
    def fill_userinput_form(element: WebElement, 
                            text: str, clear_existing: bool=True) -> None:
        """
        Fill a user input form element with the specified text.

        Args:
            element (WebElement): The input form element.
            text (str): The text to fill in the form element.
            clear_existing (bool): Whether to clear existing text before filling.\
                Defaults to True.
        """
        if clear_existing:
            element.clear()
        element.send_keys(text)
        
        return None
    
    @cached_property
    def __base_session(self) -> RequestsSession:
        _s = RequestsSession(log=False, retries=5)
        return _s
    
    @property
    def session(self) -> RequestsSession:
        driver = self.driver
        s = self.__base_session
        s.update_cookies(driver.get_cookies())
        s.update_header({
        "Accept-Language": driver.execute_script("return window.navigator.language;"),
        "X-Forwarded-For": driver.execute_script("return window.navigator.ip;"),
        "X-Timezone": driver.execute_script("return window.navigator.timezone;"),
        "User-Agent": driver.execute_script("return window.navigator.userAgent;"),
        })
        return s

    @staticmethod
    def find_element_by_text(elements:list[WebElement], text: str) -> WebElement | None:
        """
        Finds a WebElement from a list based on its text content.

        Args:
            elements (List[WebElement]): The list of WebElements to search through.
            text (str): The text to match against the elements' text content.

        Returns:
            WebElement or None: The first WebElement that matches the provided text,\
                or None if no match is found.
        """
        for element in elements:
            if element.text.strip() == text:
                return element
        return None
    
    def find_button_by_text(self, text: str) -> WebElement | None:
        return self.find_element_by_text(self.driver.find_elements(By.TAG_NAME, 'button'), text)
    
    def scroll(self, direction: Literal["top", "bottom"] = "bottom", 
                alternative_method: bool = False) -> None:
        """
        Scroll the webpage to the specified direction.
        Args:
            direction (Literal["top", "bottom"]): The direction to scroll. Valid 
                values are "top" and "bottom". Defaults to "bottom"
            alternative_method (bool): Uses `Keys` to scroll. Defaults to False.
        """
        _el = self.driver.find_element(By.TAG_NAME, 'div')
        match direction:
            case "top":
                if alternative_method:
                    _el.send_keys(Keys.HOME)
                else:
                    self.driver.execute_script("window.scrollTo(0, 0)")
                
            case "bottom":
                if alternative_method:
                    _el.send_keys(Keys.END)
                else:
                    self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")  # noqa: E501
                    
    @property
    def soup(self) -> BeautifulSoup:
        """Returns soup object of current page"""
        return BeautifulSoup(self.driver.page_source, 'html.parser')
    
    def halfscreen(self) -> None:
        """Set browser to half screen width"""
        driver = self.driver
        size = driver.get_window_size()
        driver.set_window_size(size['width']/2, size['height'])
        driver.set_window_position(size['width']/2-13, 0)
        
    def _prep_driver(self, useragent: str) -> None:
        driver = self.driver
        driver.implicitly_wait(self.IMPLICITLY_WAIT_TIME) 
        driver.execute_script('window.focus()')
        driver.execute_cdp_cmd('Network.setUserAgentOverride',
                                {"userAgent": useragent})
        driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument",
        {
            "source": """
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined
                })
                """})
        driver.execute_cdp_cmd("Network.enable", {})
        driver.execute_cdp_cmd("Network.setExtraHTTPHeaders",
                                {"headers": {"User-Agent": useragent}})
        
    def get(self, url: str) -> None:
        """Navigate to webpage"""
        try:
            if '://' not in url:
                url = 'https://' + url
            self.driver.get(url)
            WebDriverWait(self.driver, timeout=self.MAX_WAIT_TIME, poll_frequency=0.5)
        except Exception as e:
            print(str(e))

def latest_useragent(browser: str) -> str:
    """Returns the latest useragent for the specified browser"""
    try:
        useragents: list[str] = requests.get('https://jnrbsn.github.io/user-agents/user-agents.json').json()
        for useragent in useragents:
            if browser.casefold() in useragent.casefold():
                return useragent
    except Exception as e:
        print(str(e))
    return ''
