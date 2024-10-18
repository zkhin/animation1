

"""
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import logging

class HeliumLikeActions:
    def __init__(self, driver: iOSWebDriver):
        self.driver = driver
        self.action_log = []

    def log_action(self, action_type, details):
        action = {
            'timestamp': time.time(),
            'action_type': action_type,
            'details': details
        }
        self.action_log.append(action)
        logging.info(f"Action recorded: {json.dumps(action)}")

    def click(self, element: Union[WebElement, str], timeout=10):
        if isinstance(element, str):
            try:
                element_to_click = WebDriverWait(self.driver, timeout).until(
                    EC.presence_of_element_located((By.XPATH, f"//*[contains(text(), '{element}')]"))
                )
                element_to_click.click()
                self.log_action('click', {'element_text': element})
            except NoSuchElementException:
                logging.error(f'Element with text "{element}" not found.')
            except Exception as e:
                logging.error(f'An unexpected error occurred: {str(e)}')
        else:
            try:
                element.click()
                self.log_action('click', {'element_id': element.id})
            except Exception as e:
                logging.error(f'An unexpected error occurred: {str(e)}')

    def write(self, text: str, into: Union[WebElement, str] = None, timeout=10):
        if into:
            if isinstance(into, str):
                try:
                    element_to_write = WebDriverWait(self.driver, timeout).until(
                        EC.presence_of_element_located((By.XPATH, f"//input[@placeholder='{into}']"))
                    )
                    element_to_write.send_keys(text)
                    self.log_action('write', {'text': text, 'into': into})
                except NoSuchElementException:
                    logging.error(f'Element with placeholder "{into}" not found.')
                except Exception as e:
                    logging.error(f'An unexpected error occurred: {str(e)}')
            else:
                try:
                    into.send_keys(text)
                    self.log_action('write', {'text': text})
                except Exception as e:
                    logging.error(f'An unexpected error occurred: {str(e)}')
        else:
            logging.error(f'No element specified for writing text: "{text}"')

"""

import ui
import time
import objc_util
import logging
import json
from objc_util import ObjCClass, ObjCInstance, on_main_thread
from selenium.webdriver.remote.webdriver import WebDriver as RemoteWebDriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException, TimeoutException, WebDriverException
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.common.keys import Keys
from bs4 import BeautifulSoup
from typing import Literal, Union
from functools import cached_property
from selenium.webdriver.common.action_chains import ActionChains
# ObjC bridge to WebKit
WKWebView = ObjCClass('WKWebView')
WKWebViewConfiguration = ObjCClass('WKWebViewConfiguration')
NSURLRequest = ObjCClass('NSURLRequest')
NSURL = ObjCClass('NSURL')

# Configure logging
logging.basicConfig(filename='ios_webdriver_user_actions.log', level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
from selenium.webdriver.iOS.options import Options  # or use ChromeOptions if you're using Chrome

class iOSWebDriver(RemoteWebDriver):
    MAX_WAIT_TIME: float = 10
    IMPLICITLY_WAIT_TIME: float = 3
    EXCEPTIONS = WebDriverException
    session_id = 1
    command_executor = iOS


    def __init__(self, timeout=10):
        self._timeout = timeout
        self.view = None
        self.webview = None
        self.create_webview()
        self.action_log = []
        logging.info('iOSWebDriver initialized.')
        
        logging.info('iOSWebDriver initialized.')

    @on_main_thread
    def create_webview(self):
        try:
            screen_width, screen_height = ui.get_screen_size()
            frame = (0, 0, screen_width, screen_height)
            self.view = ui.View(frame=frame)

            WKWebViewConfiguration = ObjCClass('WKWebViewConfiguration')
            config = WKWebViewConfiguration.new()
            
            WKWebView = ObjCClass('WKWebView')
            self.webview = WKWebView.alloc().initWithFrame_configuration_(((0, 0), (frame[2], frame[3])), config)

            ObjCInstance(self.view).addSubview_(self.webview)

            # Present the view
            self.view.present('panel', hide_title_bar=True)
            logging.info('WebView created and presented successfully.')
        except Exception as e:
            logging.error(f'Error creating WebView: {str(e)}')
            raise

    @on_main_thread
    def load_url(self, url):
        request = NSURLRequest.requestWithURL_(NSURL.URLWithString_(url))
        self.webview.loadRequest_(request)
        logging.info(f'URL loaded: {url}')
    @on_main_thread
    def _execute_webkit(self, func):
        try:
            return func()
        except Exception as e:
            logging.error(f"Error executing WebKit function: {str(e)}")
            raise
    def get(self, url):
        logging.info(f'Navigating to URL: {url}')
        try:
            request = ObjCClass('NSURLRequest').requestWithURL_(ObjCClass('NSURL').URLWithString_(url))
            self.webview.loadRequest_(request)
            self._wait_for_page_load()
            self.log_action('navigate', {'url': url})
        except Exception as e:
            logging.error(f'Error navigating to URL {url}: {str(e)}')
            raise

    @on_main_thread
    def _load_url(self, url):
        request = NSURLRequest.requestWithURL_(NSURL.URLWithString_(url))
        self.webview.loadRequest_(request)
        logging.info(f'URL loaded: {url}')

    def _wait_for_page_load(self, timeout=None):
        if timeout is None:
            timeout = self._timeout
        end_time = time.time() + timeout
        while time.time() < end_time:
            if not self._execute_webkit(lambda: self.webview.loading()):
                logging.info('Page load completed.')
                return
            time.sleep(0.1)
        logging.warning('Page load timeout.')
        raise TimeoutException("Page load timeout")


    def find_element(self, by=(By.ID,By.XPATH), value=None):
        logging.info(f'Attempting to find element by {by} with value: {value}')
        try:
            if by == By.NAME:
                js = f""" var elements = document.getElementsByName("{value}");  return elements.length > 0 ? elements[0] : null;  """
            elif by == By.ID:
                js = f'return document.getElementById("{value}");'
            elif by == By.CSS_SELECTOR:
                js = f'return document.querySelector("{value}");'
            elif by == By.XPATH:
                js =f""" var result = document.evaluate("{value}", document, null, XPathResult.FIRST_ORDERED_NODE_TYPE, null);   return result.singleNodeValue;  """
            else:
                raise NotImplementedError(f"Locator strategy {by} not implemented")

            element = self._execute_webkit(lambda: self.webview.evaluateJavaScript_completionHandler_(js, None))
            if element:
                logging.info(f'Element found by {by} with value: {value}')
                return iOSWebElement(self, element)
            else:
                logging.warning(f'No element found by {by} with value: {value}')
                raise NoSuchElementException(f"No element found with locator: {by}={value}")
        except Exception as e:
            logging.error(f'Error finding element: {str(e)}')
            raise
    def find_elements(self, by=By.ID, value=None):
        logging.info(f'User is attempting to find elements by {by} with value: {value}')
        try:
            elements = self._find_elements(by, value)
            logging.info(f'{len(elements)} elements found by {by} with value: {value}')
            return elements
        except NoSuchElementException:
            logging.warning(f'Elements not found by {by} with value: {value}')
            raise

    def _find_element(self, by, value):
        js_locator = self._get_js_locator(by, value)
        return self._execute_webkit(lambda: self._find_element_by_js(js_locator))

    def _find_elements(self, by, value):
        js_locator = self._get_js_locator(by, value, multiple=True)
        return self._execute_webkit(lambda: self._find_elements_by_js(js_locator))

    def _get_js_locator(self, by, value, multiple=False):
        if by == By.ID:
            return f'document.getElementById("{value}")'
        elif by == By.NAME:
            return f'document.getElementsByName("{value}")' if multiple else f'document.getElementsByName("{value}")[0]'
        elif by == By.CLASS_NAME:
            return f'document.getElementsByClassName("{value}")' if multiple else f'document.getElementsByClassName("{value}")[0]'
        elif by == By.CSS_SELECTOR:
            return f'document.querySelectorAll("{value}")' if multiple else f'document.querySelector("{value}")'
        elif by == By.XPATH:
            return f'document.evaluate("{value}", document, null, XPathResult.FIRST_ORDERED_NODE_TYPE, null).singleNodeValue'
        else:
            raise NotImplementedError(f"Locator strategy {by} not implemented")

    @on_main_thread
    def _find_element_by_js(self, js):
        result = self.webview.evaluateJavaScript_completionHandler_(js, None)
        if result:
            logging.info(f'JavaScript executed successfully to find element: {js}')
            return iOSWebElement(self, result)
        raise NoSuchElementException(f"No element found with JavaScript locator: {js}")

    @on_main_thread
    def _find_elements_by_js(self, js):
        results = self.webview.evaluateJavaScript_completionHandler_(js, None)
        if results:
            logging.info(f'JavaScript executed successfully to find elements: {js}, count: {len(results)}')
            return [iOSWebElement(self, result) for result in results]
        logging.info(f'No elements found with JavaScript locator: {js}')
        return []

    def back(self):
        logging.info('User navigated back.')
        self._execute_webkit(lambda: self.webview.goBack())

    def forward(self):
        logging.info('User navigated forward.')
        self._execute_webkit(lambda: self.webview.goForward())

    def refresh(self):
        logging.info('User refreshed the page.')
        self._execute_webkit(lambda: self.webview.reload())

    def get_title(self):
        title = self.execute_script("return document.title;")
        logging.info(f'User retrieved page title: {title}')
        return title

    def get_current_url(self):
        current_url = self._execute_webkit(lambda: str(self.webview.URL()))
        logging.info(f'User retrieved current URL: {current_url}')
        return current_url

    def save_screenshot(self, filename):
        logging.info(f'User saved a screenshot to {filename}.')
        img = self._execute_webkit(lambda: self._capture_screenshot())
        with open(filename, 'wb') as f:
            f.write(img)

    @on_main_thread
    def _capture_screenshot(self):
        uiimage = self.webview.snapshotView().asImage()
        return uiimage.jpegData(1.0)
    import json  # Import the json module for serialization

    def handle_touch(self, touch):
        x, y = touch.location
        element = self.execute_script(f"""var element = document.elementFromPoint({x}, {y});if (element) {{return {{tagName: element.tagName, id: element.id,className: element.className,text: element.textContent.trim() }};}}return null;""")
        # Properly close the JavaScript string
    
        if element:
            print(f"Hovered over: {json.dumps(element, indent=2)}")
            logging.info(f'User hovered over element: {json.dumps(element)}')
        else:
            logging.info('No element found at the touch location.')

    def log_action(self, action, element_info):
        log_entry = {
            'timestamp': time.time(),
            'action': action,
            'element': element_info
        }
        self.action_log.append(log_entry)
        logging.info(f'Action logged: {json.dumps(log_entry)}')

    def get(self, url):
        logging.info(f'User navigated to URL: {url}')
        self._execute_webkit(lambda: self._load_url(url))
        self._wait_for_page_load()
        self.log_action('navigate', {'url': url})

    def find_element(self, by=By.ID, value=None):
        logging.info(f'User is attempting to find element by {by} with value: {value}')
        try:
            element = self._find_element(by, value)
            logging.info(f'Element found by {by} with value: {value}')
            self.log_action('find_element', {'by': by, 'value': value})
            return element
        except NoSuchElementException:
            logging.warning(f'Element not found by {by} with value: {value}')
            raise

    def execute_script(self, script, *args):
        logging.info(f'User executed script: {script}')
        result = self._execute_webkit(lambda: self._execute_script(script, *args))
        self.log_action('execute_script', {'script': script})
        return result

    def implicitly_wait(self, time_to_wait):
        self._timeout = time_to_wait
        logging.info(f'User set implicit wait timeout to {time_to_wait} seconds.')

    def quit(self):
        logging.info('User quit the iOSWebDriver.')
        self._execute_webkit(lambda: self.view.close())

    def save_action_log(self, filename='action_log.json'):
        with open(filename, 'w') as f:
            json.dump(self.action_log, f, indent=2)
        logging.info(f'Action log saved to {filename}')

class iOSWebElement:
    def __init__(self, parent, element_id):
        self.parent = parent
        self.id = element_id

    def click(self):
        logging.info(f'User clicked on element with ID: {self.id}')
        self.parent.execute_script(f'document.getElementById("{self.id}").click();')
        self.parent.log_action('click', {'element_id': self.id})

    def is_displayed(self):
        displayed = self.parent.execute_script(f'return document.getElementById("{self.id}").offsetParent !== null;')
        logging.info(f'Element with ID: {self.id} is displayed: {displayed}')
        return displayed
    def send_keys(self, text):
        logging.info(f'User sent keys to element with ID: {self.id}, text: {text}')
        self.parent.execute_script(f'document.getElementById("{self.id}").value = "{text}";')
        self.parent.log_action('send_keys', {'element_id': self.id, 'text': text})

    def get_attribute(self, name):
        attribute_value = self.parent.execute_script(f'return document.getElementById("{self.id}").getAttribute("{name}");')
        logging.info(f'User got attribute: {name} of element with ID: {self.id}, value: {attribute_value}')
        return attribute_value

    def get_text(self):
        text = self.parent.execute_script(f'return document.getElementById("{self.id}").textContent;')
        logging.info(f'User got text of element with ID: {self.id}, text: {text}')
        return text

    def clear(self):
        logging.info(f'User cleared text of element with ID: {self.id}')
        self.parent.execute_script(f'document.getElementById("{self.id}").value = "";')
        self.parent.log_action('clear', {'element_id': self.id})

    def quit(self):
        logging.info('User quit the iOSWebDriver.')
        self._execute_webkit(lambda: self.view.close())
        
    def wait_for_locator(self, locator: tuple[str, str]) -> None:
        logging.info(f'Waiting for locator: {locator}')
        WebDriverWait(self, self.MAX_WAIT_TIME, 0.5).until(EC.presence_of_element_located(locator))
        logging.info(f'Locator found: {locator}')

    @staticmethod
    def fill_userinput_form(element: WebElement, text: str, clear_existing: bool = True) -> None:
        logging.info(f'Filling form element with text: {text}')
        if clear_existing:
            element.clear()
        element.send_keys(text)
        logging.info('Form filled successfully')

    @cached_property
    def __base_session(self):
        # This is a placeholder. In iOS/Pythonista, we might need a different approach for session management
        logging.info('Creating base session')
        return {}

    @property
    def session(self):
        # This is a placeholder. We'll need to implement custom session management for iOS/Pythonista
        logging.info('Accessing session')
        return self.__base_session

    @staticmethod
    def find_element_by_text(elements: list[WebElement], text: str) -> Union[WebElement, None]:
        logging.info(f'Searching for element with text: {text}')
        for element in elements:
            if element.text.strip() == text:
                logging.info(f'Element found with text: {text}')
                return element
        logging.info(f'No element found with text: {text}')
        return None

    def find_button_by_text(self, text: str) -> Union[WebElement, None]:
        logging.info(f'Searching for button with text: {text}')
        return self.find_element_by_text(self.find_elements(By.TAG_NAME, 'button'), text)

    def scroll(self, direction: Literal["top", "bottom"] = "bottom", alternative_method: bool = False) -> None:
        logging.info(f'Scrolling to {direction}')
        if direction == "top":
            js = "window.scrollTo(0, 0)" if not alternative_method else "arguments[0].scrollIntoView(true);"
        else:
            js = "window.scrollTo(0, document.body.scrollHeight);" if not alternative_method else "arguments[0].scrollIntoView(false);"
        
        element = self.find_element(By.TAG_NAME, 'body')
        self.execute_script(js, element)
        logging.info(f'Scrolled to {direction}')

    @property
    def soup(self) -> BeautifulSoup:
        logging.info('Creating BeautifulSoup object of current page')
        return BeautifulSoup(self.page_source, 'html.parser')

    def halfscreen(self) -> None:
        logging.info('Setting browser to half screen width')
        size = self.get_window_size()
        self.set_window_size(size['width'] // 2, size['height'])
        self.set_window_position(size['width'] // 2 - 13, 0)

    def _prep_driver(self, useragent: str) -> None:
        logging.info(f'Preparing driver with user agent: {useragent}')
        self.implicitly_wait(self.IMPLICITLY_WAIT_TIME)
        self.execute_script('window.focus()')
        # Note: CDP commands might not work in iOS WebKit. We'll need to find iOS-specific alternatives.
        logging.info('Driver preparation complete')

    def get(self, url: str) -> None:
        logging.info(f'Navigating to URL: {url}')
        if '://' not in url:
            url = 'https://' + url
        super().get(url)
        WebDriverWait(self, timeout=self.MAX_WAIT_TIME, poll_frequency=0.5).until(
            lambda driver: driver.execute_script('return document.readyState') == 'complete'
        )
        logging.info(f'Navigation to {url} complete')

from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import logging
class HeliumLikeActions:
    def __init__(self, driver: iOSWebDriver):
        self.driver = driver
        self.action_log = []

    def log_action(self, action_type, details):
        action = {
            'timestamp': time.time(),
            'action_type': action_type,
            'details': details
        }
        self.action_log.append(action)
        logging.info(f"Action recorded: {json.dumps(action)}")

    def click(self, element: Union[WebElement, str]):
        if isinstance(element, str):
            try:
                element = WebDriverWait(self.driver, 10).until(
                    EC.presence_of_element_located((By.XPATH, f"//*[contains(text(), '{element}')]"))
                )
                element.click()
                self.log_action('click', {'element_text': element.text})
            except NoSuchElementException:
                logging.error(f'Element with text "{element}" not found.')
        else:
            element.click()
            self.log_action('click', {'element_id': element.id})

    def write(self, text: str, into: Union[WebElement, str] = None):
        if into:
            if isinstance(into, str):
                try:
                    # Wait for the element to be present
                    into_element = WebDriverWait(self.driver, 10).until(
                        EC.presence_of_element_located((By.XPATH, f"//input[@placeholder='{into}']"))
                    )
                    into_element.send_keys(text)
                    self.log_action('write', {'text': text, 'into': into})
                except NoSuchElementException:
                    logging.error(f'Element with placeholder "{into}" not found.')
            else:
                into.send_keys(text)
                self.log_action('write', {'text': text})
        else:
            logging.error(f'No element specified for writing text: "{text}"')

    def press(self, key):
        actions = ActionChains(self.driver)
        actions.send_keys(key).perform()
        self.log_action('press', {'key': key})
def install_ios_webdriver():
    try:
        from selenium import webdriver
        webdriver.iOSWebDriver = iOSWebDriver
        logging.info('iOSWebDriver installed successfully.')
    except ImportError:
        logging.error('Error: Selenium is not installed. Please install Selenium first.')
    except Exception as e:
        logging.error(f'An error occurred while installing iOSWebDriver: {str(e)}')

# Example usage
if __name__ == "__main__":
    driver = iOSWebDriver()
    actions = HeliumLikeActions(driver)

    try:
        
        driver.get("https://www.example.com")
#        actions.click("Log In")
#        actions.write("username", into="Username")
#        actions.write("password", into="Password")
        actions.press(Keys.ENTER)
#        
#        # Wait for page to load after login
#        driver.wait_for_locator((By.ID, "welcome-message"))
#        
#        print("Logged in successfully!")

        
    except Exception as e:
        logging.error(f"An error occurred: {str(e)}")
        print(f"An error occurred: {str(e)}")
    finally:
        driver.quit()
