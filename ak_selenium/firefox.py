from helium import start_firefox
from selenium import webdriver

import logging
import os

from ak_selenium.browser import Browser, latest_useragent

#Disable webdriver-manager logs per https://github.com/SergeyPirogov/webdriver_manager#wdm_log
os.environ['WDM_LOG'] = str(logging.NOTSET)

class Firefox(Browser):
    USERAGENT: str = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/120.0'

    def __init__(self, headless:bool = False, 
        userdata_path:str|None=None, half_screen:bool=True) -> None:
        
        _useragent: str = latest_useragent('Firefox')
        if _useragent != '':
            self.USERAGENT = _useragent
        
        self.headless = headless
        self.half_screen = half_screen
        self.userdata_path = userdata_path
                
        self.driver: webdriver.Firefox = self._driver()
        super().__init__(driver=self.driver)
        self._prep_driver(useragent=self.USERAGENT)
        
        if half_screen:
            self.halfscreen()
        return None
    
    
    def __str__(self) -> str:
        return f"""
        Friefox.Object
        UserAgent:{self.USERAGENT}
        Implicit Wait Time: {self.IMPLICITLY_WAIT_TIME:.2f}s
        Max Wait Time: {self.MAX_WAIT_TIME:.2f}s
        Headless: {self.headless}
        Userdata Path: {self.userdata_path}
        Half Screen View: {self.half_screen}
        """
    
    def __repr__(self) -> str:
        return f"Firefox(headless={self.headless},\
                userdata_path={self.userdata_path},\
                half_screen={self.half_screen})"

    def _driver(self) -> webdriver.Firefox:
        """
        Initializes a Firefox web driver with specific options and configurations.
        
        Returns:
            webdriver.Firefox: The initialized Chrome driver object.
        """
        driver = start_firefox(url=None, headless=self.headless, options=self.options, profile=self.profile)
        return driver # type: ignore
    
    @property
    def profile(self) -> webdriver.FirefoxProfile:
        profile = webdriver.FirefoxProfile()
        profile.set_preference("general.useragent.override", self.USERAGENT)
        return profile
        
    @property
    def options(self) -> webdriver.FirefoxOptions:
        options = webdriver.FirefoxOptions()
        options.add_argument('--disable-gpu')
        if self.headless:
            options.add_argument("--width=1920")
            options.add_argument("--height=1080")
        options.add_argument("start-maximized")
        
        return options