


import ui
import webbrowser
import asyncio
import objc_util
import threading
from objc_util import ObjCClass, ObjCInstance, create_objc_class, on_main_thread
from selenium.webdriver.remote.webdriver import WebDriver as RemoteWebDriver
from selenium.webdriver.remote.webelement import WebElement as RemoteWebElement
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import (
    NoSuchElementException, TimeoutException, WebDriverException,
    ElementNotVisibleException, ElementNotInteractableException
)
import time
import re

# Bridge to WebKit
WKWebView = ObjCClass('WKWebView')
WKWebViewConfiguration = ObjCClass('WKWebViewConfiguration')
NSURLRequest = ObjCClass('NSURLRequest')
NSURL = ObjCClass('NSURL')

from selenium.webdriver.remote.webdriver import WebDriver as RemoteWebDriver

class iOSWebDriver(RemoteWebDriver):
    def __init__(self, timeout=20):
        # Initialize without calling the superclass constructor
        self._timeout = timeout
        self.view = None
        self.webview = None
        self.create_webview()
        
        # Set up command_executor and w3c_compliant flag
        self.command_executor = 'http://localhost:0'  # Dummy URL
        self.w3c_compliant = True


    @on_main_thread
    def create_webview(self):
        try:
            # Use the main screen's bounds for the frame
            screen_width = ui.get_screen_size().width
            screen_height = ui.get_screen_size().height
            frame = (0, 0, screen_width, screen_height)
            print(f"Screen size: {ui.get_screen_size()}")
            print(f"Frame: {frame}")
            
            self.view = ui.View(frame=frame)
            print("ui.View created")
            
            config = WKWebViewConfiguration.new()
            print("WKWebViewConfiguration created")
            
            self.webview = WKWebView.alloc().initWithFrame_configuration_(
                ((0, 0), (frame[2], frame[3])), config)
            print("WKWebView created")
            
            ObjCInstance(self.view).addSubview_(self.webview)
            print("WebView added to View")
            
            # Present view synchronously
            @on_main_thread
            def present_view():
                self.view.present('panel', hide_title_bar=True)
                print("View presented")
            
            present_view()
            
            # Wait for the view to be presented
            start_time = time.time()
            while not self.view.on_screen:
        
                if time.time() - start_time > 1:  # 5 second timeout
                    raise TimeoutException("Timeout while presenting the WebView")
            
            print("WebView creation completed successfully")
            
        except Exception as e:
            print(f"Error creating WebView: {str(e)}")
            raise
    def get(self, url):
        self._execute_webkit(lambda: self._load_url(url))
        
        # Ensure the page loading is properly awaited
        asyncio.run(self._wait_for_page_load())
    @on_main_thread
    def _load_url(self, url):
        request = NSURLRequest.requestWithURL_(NSURL.URLWithString_(url))
        self.webview.loadRequest_(request)
    
    async def _wait_for_page_load(self, timeout=None):
        if timeout is None:
            timeout = 5  # Default timeout of 5 seconds
        end_time = time.time() + timeout
        while time.time() < end_time:
            # Ensure the webview is done loading
            if not self._execute_webkit(lambda: self.webview.loading()):
                return
            await asyncio.sleep(0.1)  # Await for 100ms before checking again
        raise TimeoutException("Timeout waiting for page load")

    def find_element(self, by=By.ID, value=None):
        return self._find_element(by, value)

    def find_elements(self, by=By.ID, value=None):
        return self._find_elements(by, value)
    @on_main_thread
    def _find_element_by_name(self, name):
        """Find a single element by its name attribute."""
        js = f'document.getElementsByName("{name}")[0]'
        result = self.webview.evaluateJavaScript_completionHandler_(js, None)
        if result:
            return iOSWebElement(self, result['id'], By.NAME)
        raise NoSuchElementException(f"No element found with name: {name}")
    @on_main_thread
    def _find_elements_by_name(self, name):
        """Find multiple elements by their name attribute."""
        js = f'Array.from(document.getElementsByName("{name}"))'
        results = self.webview.evaluateJavaScript_completionHandler_(js, None)
        return [iOSWebElement(self, result['id'], By.NAME) for result in results] if results else []
    def _find_element(self, by, value):
        if by == By.ID:
            return self._execute_webkit(lambda: self._find_element_by_id(value))
        elif by == By.CLASS_NAME:
            return self._execute_webkit(lambda: self._find_element_by_class_name(value))
        elif by == By.CSS_SELECTOR:
            return self._execute_webkit(lambda: self._find_element_by_css_selector(value))
        elif by == By.XPATH:
            return self._execute_webkit(lambda: self._find_element_by_xpath(value))
        elif by == By.NAME:
            return self._execute_webkit(lambda: self._find_element_by_name(value))
        else:
            raise NotImplementedError(f"Locator strategy {by} is not implemented")
    
    def _find_elements(self, by, value):
        if by == By.ID:
            return self._execute_webkit(lambda: self._find_elements_by_id(value))
        elif by == By.CLASS_NAME:
            return self._execute_webkit(lambda: self._find_elements_by_class_name(value))
        elif by == By.CSS_SELECTOR:
            return self._execute_webkit(lambda: self._find_elements_by_css_selector(value))
        elif by == By.XPATH:
            return self._execute_webkit(lambda: self._find_elements_by_xpath(value))
        elif by == By.NAME:
            return self._execute_webkit(lambda: self._find_elements_by_name(value))
        else:
            raise NotImplementedError(f"Locator strategy {by} is not implemented")
    @on_main_thread
    def _find_element_by_id(self, element_id):
        js = f'document.getElementById("{element_id}")'
        result = self.webview.evaluateJavaScript_completionHandler_(js, None)
        if result:
            return iOSWebElement(self, element_id, By.ID)
        raise NoSuchElementException(f"No element found with id: {element_id}")

    @on_main_thread
    def _find_elements_by_id(self, element_id):
        js = f'Array.from(document.querySelectorAll("[id=\'{element_id}\']"))'
        results = self.webview.evaluateJavaScript_completionHandler_(js, None)
        return [iOSWebElement(self, result['id'], By.ID) for result in results] if results else []

    @on_main_thread
    def _find_element_by_class_name(self, class_name):
        js = f'document.getElementsByClassName("{class_name}")[0]'
        result = self.webview.evaluateJavaScript_completionHandler_(js, None)
        if result:
            return iOSWebElement(self, result['id'], By.CLASS_NAME)
        raise NoSuchElementException(f"No element found with class name: {class_name}")

    @on_main_thread
    def _find_elements_by_class_name(self, class_name):
        js = f'Array.from(document.getElementsByClassName("{class_name}"))'
        results = self.webview.evaluateJavaScript_completionHandler_(js, None)
        return [iOSWebElement(self, result['id'], By.CLASS_NAME) for result in results] if results else []

    @on_main_thread
    def _find_element_by_css_selector(self, css_selector):
        js = f'document.querySelector("{css_selector}")'
        result = self.webview.evaluateJavaScript_completionHandler_(js, None)
        if result:
            return iOSWebElement(self, result['id'], By.CSS_SELECTOR)
        raise NoSuchElementException(f"No element found with CSS selector: {css_selector}")

    @on_main_thread
    def _find_elements_by_css_selector(self, css_selector):
        js = f'Array.from(document.querySelectorAll("{css_selector}"))'
        results = self.webview.evaluateJavaScript_completionHandler_(js, None)
        return [iOSWebElement(self, result['id'], By.CSS_SELECTOR) for result in results] if results else []
    @on_main_thread
    def find_element_by_value(self, value):
        """Find a single element by its value attribute."""
        js = f'document.querySelector("[value=\'{value}\']")'
        result = self.webview.evaluateJavaScript_completionHandler_(js, None)
        if result:
            return iOSWebElement(self, result)
        raise NoSuchElementException(f"No element found with value: {value}")
    
    @on_main_thread
    def find_elements_by_value(self, value):
        """Find multiple elements by their value attribute."""
        js = f'document.querySelectorAll("[value=\'{value}\']")'
        results = self.webview.evaluateJavaScript_completionHandler_(js, None)
        return [iOSWebElement(self, result) for result in results] if results else []
    def _find_element_by_xpath(self, xpath):
        js = f'''
        var result = document.evaluate('{xpath}', document, null, XPathResult.FIRST_ORDERED_NODE_TYPE, null);
        result.singleNodeValue;
        '''
        result = self.webview.evaluateJavaScript_completionHandler_(js, None)
        if result:
            return iOSWebElement(self, result['id'], By.XPATH)
        raise NoSuchElementException(f"No element found with XPath: {xpath}")

    @on_main_thread
    def _find_elements_by_xpath(self, xpath):
        js = f'''
        var result = document.evaluate('{xpath}', document, null, XPathResult.ORDERED_NODE_SNAPSHOT_TYPE, null);
        var elements = [];
        for (var i = 0; i < result.snapshotLength; i++) {{
            elements.push(result.snapshotItem(i));
        }}
        elements;
        '''
        results = self.webview.evaluateJavaScript_completionHandler_(js, None)
        return [iOSWebElement(self, result['id'], By.XPATH) for result in results] if results else []

    def execute_script(self, script, *args):
        return self._execute_webkit(lambda: self._execute_script(script, *args))

    @on_main_thread
    def _execute_script(self, script, *args):
        # Basic argument substitution (improve as needed)
        for i, arg in enumerate(args):
            if isinstance(arg, iOSWebElement):
                script = script.replace(f"arguments[{i}]", f"document.getElementById('{arg.id}')")
            else:
                script = script.replace(f"arguments[{i}]", repr(arg))
        return self.webview.evaluateJavaScript_completionHandler_(script, None)
    def _execute_webkit(self, command):
        result = []
        error = []
        def run_on_main_thread():
            try:
                result.append(command())
            except Exception as e:
                error.append(e)
        objc_util.on_main_thread(run_on_main_thread)()
        if error:
            raise error[0]
        return result[0] if result else None
        objc_util.on_main_thread(run_on_main_thread)()
        if error:
            raise error[0]
        return result[0] if result else None

    def implicitly_wait(self, time_to_wait):
        self.timeout = time_to_wait
    def back(self):
        self._execute_webkit(lambda: self.webview.goBack())

    def forward(self):
        self._execute_webkit(lambda: self.webview.goForward())

    def refresh(self):
        self._execute_webkit(lambda: self.webview.reload())

    def get_title(self):
        return self.execute_script("return document.title;")

    def get_current_url(self):
        return self._execute_webkit(lambda: str(self.webview.URL()))

    def save_screenshot(self, filename):
        img = self._execute_webkit(lambda: self._capture_screenshot())
        with open(filename, 'wb') as f:
            f.write(img)

    @on_main_thread
    def _capture_screenshot(self):
        uiimage = self.webview.snapshotView().asImage()
        return uiimage.jpegData(1.0)

    def set_window_size(self, width, height):
        def resize():
            frame = self.view.frame
            frame.width = width
            frame.height = height
            self.view.frame = frame
            self.webview.frame = ((0, 0), (width, height))
        self._execute_webkit(resize)
    def quit(self):
        self._execute_webkit(lambda: self.view.close())

class iOSWebElement(RemoteWebElement):
    def __init__(self, parent, id_, by):
        super().__init__(parent, id_)
        self._by = by

    def click(self):
        self._execute_webkit(lambda: self._click())

    @on_main_thread
    def _click(self):
        js = f'''
        var element = document.getElementById('{self.id}');
        if (element) {{
            if (element.offsetParent !== null) {{
                element.click();
            }} else {{
                throw new Error('Element is not visible');
            }}
        }} else {{
            throw new Error('Element not found');
        }}
        '''
        try:
            self.parent.execute_script(js)
        except WebDriverException as e:
            if 'Element is not visible' in str(e):
                raise ElementNotVisibleException(f"Element with id {self.id} is not visible")
            elif 'Element not found' in str(e):
                raise NoSuchElementException(f"Element with id {self.id} not found")
            else:
                raise

    def send_keys(self, *value):
        text = ''.join(value)
        self._execute_webkit(lambda: self._send_keys(text))

    @on_main_thread
    def _send_keys(self, text):
        js = f'''
        var element = document.getElementById('{self.id}');
        if (element) {{
            if (element.offsetParent !== null) {{
                if (element.tagName === 'INPUT' || element.tagName === 'TEXTAREA' || element.isContentEditable) {{
                    element.value = "{text}";
                    var event = new Event('input', {{ bubbles: true }});
                    element.dispatchEvent(event);
                }} else {{
                    throw new Error('Element is not interactable');
                }}
            }} else {{
                throw new Error('Element is not visible');
            }}
        }} else {{
            throw new Error('Element not found');
        }}
        '''
        try:
            self.parent.execute_script(js)
        except WebDriverException as e:
            if 'Element is not visible' in str(e):
                raise ElementNotVisibleException(f"Element with id {self.id} is not visible")
            elif 'Element is not interactable' in str(e):
                raise ElementNotInteractableException(f"Element with id {self.id} is not interactable")
            elif 'Element not found' in str(e):
                raise NoSuchElementException(f"Element with id {self.id} not found")
            else:
                raise

    def clear(self):
        self._execute_webkit(lambda: self._clear())

    @on_main_thread
    def _clear(self):
        js = f'''
        var element = document.getElementById('{self.id}');
        if (element) {{
            if (element.offsetParent !== null) {{
                if (element.tagName === 'INPUT' || element.tagName === 'TEXTAREA') {{
                    element.value = '';
                    var event = new Event('input', {{ bubbles: true }});
                    element.dispatchEvent(event);
                }} else {{
                    throw new Error('Element is not clearable');
                }}
            }} else {{
                throw new Error('Element is not visible');
            }}
        }} else {{
            throw new Error('Element not found');
        }}
        '''
        try:
            self.parent.execute_script(js)
        except WebDriverException as e:
            if 'Element is not visible' in str(e):
                raise ElementNotVisibleException(f"Element with id {self.id} is not visible")
            elif 'Element is not clearable' in str(e):
                raise ElementNotInteractableException(f"Element with id {self.id} is not clearable")
            elif 'Element not found' in str(e):
                raise NoSuchElementException(f"Element with id {self.id} not found")
            else:
                raise

    def is_displayed(self):
        return self._execute_webkit(lambda: self._is_displayed())

    @on_main_thread
    def _is_displayed(self):
        js = f'''
        var element = document.getElementById('{self.id}');
        if (element) {{
            return (element.offsetParent !== null);
        }} else {{
            throw new Error('Element not found');
        }}
        '''
        try:
            return self.parent.execute_script(js)
        except WebDriverException as e:
            if 'Element not found' in str(e):
                raise NoSuchElementException(f"Element with id {self.id} not found")
            else:
                raise

    def get_attribute(self, name):
        return self._execute_webkit(lambda: self._get_attribute(name))

    @on_main_thread
    def _get_attribute(self, name):
        js = f'''
        var element = document.getElementById('{self.id}');
        if (element) {{
            return element.getAttribute('{name}');
        }} else {{
            throw new Error('Element not found');
        }}
        '''
        try:
            return self.parent.execute_script(js)
        except WebDriverException as e:
            if 'Element not found' in str(e):
                raise NoSuchElementException(f"Element with id {self.id} not found")
            else:
                raise

    def _execute_webkit(self, command):
        return self.parent._execute_webkit(command)
    def get_text(self):
        return self._execute_webkit(lambda: self._get_text())

    @on_main_thread
    def _get_text(self):
        js = f'''
        var element = document.getElementById('{self.id}');
        if (element) {{
            return element.textContent;
        }} else {{
            throw new Error('Element not found');
        }}
        '''
        try:
            return self.parent.execute_script(js)
        except WebDriverException as e:
            if 'Element not found' in str(e):
                raise NoSuchElementException(f"Element with id {self.id} not found")
            else:
                raise

    def submit(self):
        self._execute_webkit(lambda: self._submit())

    @on_main_thread
    def _submit(self):
        js = f'''
        var element = document.getElementById('{self.id}');
        if (element) {{
            if (element.offsetParent !== null) {{
                var form = element.closest('form');
                if (form) {{
                    form.submit();
                }} else {{
                    throw new Error('Element is not within a form');
                }}
            }} else {{
                throw new Error('Element is not visible');
            }}
        }} else {{
            throw new Error('Element not found');
        }}
        '''
        try:
            self.parent.execute_script(js)
        except WebDriverException as e:
            if 'Element is not visible' in str(e):
                raise ElementNotVisibleException(f"Element with id {self.id} is not visible")
            elif 'Element is not within a form' in str(e):
                raise WebDriverException(f"Element with id {self.id} is not within a form")
            elif 'Element not found' in str(e):
                raise NoSuchElementException(f"Element with id {self.id} not found")
            else:
                raise

# Add a custom wait condition
class element_has_css_class(object):
    def __init__(self, locator, css_class):
        self.locator = locator
        self.css_class = css_class

    def __call__(self, driver):
        element = driver.find_element(*self.locator)
        if self.css_class in element.get_attribute("class"):
            return element
        else:
            return False
            
import json
import time
from selenium.webdriver.common.by import By

class LoggingiOSWebDriver(iOSWebDriver):
    def __init__(self):
        super().__init__()
        self.interaction_log = []  # List to hold interaction logs

    def log_action(self, action_type, element, value=None):
        """Log the action taken by the user."""
        log_entry = {
            'time': time.time(),
            'action': action_type,
            'element': element,
            'value': value
        }
        self.interaction_log.append(log_entry)
        print(f"Logged interaction: {log_entry}")

    def find_element(self, by=By.ID, value=None):
        """Override find_element to log clicks and other interactions."""
        element = super().find_element(by, value)
        
        # Wrap the element in a logging wrapper
        return LoggedWebElement(self, element, by, value)

    def save_interactions(self, filename="interaction_log.json"):
        """Save the recorded interactions to a JSON file."""
        with open(filename, 'w') as f:
            json.dump(self.interaction_log, f, indent=4)
        print(f"Interactions saved to {filename}")
import json
import time

class RecordingiOSWebDriver(iOSWebDriver):
    def __init__(self):
        super().__init__()
        self.interaction_log = []  # List to hold interaction logs

    def log_action(self, action_type, element=None, value=None):
        """Log the action taken by the user."""
        log_entry = {
            'time': time.time(),
            'action': action_type,
            'element': element,
            'value': value
        }
        self.interaction_log.append(log_entry)
        print(f"Logged interaction: {log_entry}")

    def save_log(self, filename="interaction_log.json"):
        """Save the interaction log to a JSON file."""
        with open(filename, 'w') as f:
            json.dump(self.interaction_log, f, indent=4)
        print(f"Interactions saved to {filename}")

    def get(self, url):
        """Override to log navigation actions."""
        super().get(url)
        self.log_action('navigate', url)

    def find_element(self, by=By.ID, value=None):
        """Override find_element to log actions."""
        element = super().find_element(by, value)
        return LoggedWebElement(self, element, by, value)

    def find_elements(self, by=By.ID, value=None):
        """Override find_elements to log actions."""
        elements = super().find_elements(by, value)
        return [LoggedWebElement(self, element, by, value) for element in elements]

class LoggedWebElement(iOSWebElement):
    """WebElement wrapper to log interactions."""

    def __init__(self, parent, element, by, value):
        super().__init__(parent, element)
        self.by = by
        self.value = value

    def click(self):
        """Override click to log the action."""
        super().click()
        self.parent.log_action('click', f'{self.by}="{self.value}"')

    def send_keys(self, text):
        """Override send_keys to log the action."""
        super().send_keys(text)
        self.parent.log_action('send_keys', f'{self.by}="{self.value}"', text)
def install_ios_webdriver():
    try:
        from selenium import webdriver
        webdriver.iOSWebDriver = iOSWebDriver
        print("iOSWebDriver installed successfully.")
    except ImportError:
        print("Error: Selenium is not installed. Please install Selenium first.")
    except Exception as e:
        print(f"An error occurred while installing iOSWebDriver: {str(e)}")
        
# Usage example
if __name__ == "__main__":
    #from selenium import webdriver
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    install_ios_webdriver()
    
# Initialize the recording WebDriver
driver = RecordingiOSWebDriver()

# Navigate to a website
driver.get("https://www.google.com")

# Find an element and interact with it (these actions will be logged)
#search_box = driver.find_element(By.NAME, "q")


#search_button = driver.find_element(By.NAME, "btnK")


# Save the recorded actions to a file
#driver.save_log("user_interactions.json")

# Quit the driver
#driver.quit()
"""
            # Example usage of the LoggingiOSWebDriver
    driver = LoggingiOSWebDriver()
    
    # Navigate to a website
    driver.get("https://www.example.com")
    
    # Find an element and interact with it (these actions will be logged)
    search_box = driver.find_element(By.NAME, "q")
    search_box.send_keys("Pythonista WebDriver")
    
    search_button = driver.find_element(By.NAME, "btnK")
    search_button.click()
    
    # Wait for results (this action won't be logged as it's passive)
    WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.ID, "search-results"))
    )
    
    # Save the interaction log to a file
    driver.save_interactions("user_interactions.json")
    
    # Quit the driver
    driver.quit()
"""
        
#        
#        
#        driver = webdriver.iOSWebDriver()
#        driver.get("https://www.google.com")
#    
#        search_input = driver.find_element(By.CLASS_NAME, "btn")
#        search_input.send_keys("Hello, Selenium on iOS!")
#        
#        search_button = driver.find_element(By.ID, "search-button")
#        search_button.click()
#        
#        title = driver.execute_script("return document.title;")
#        print(f"Page title: {title}")
#        search_input = WebDriverWait(driver, 10).until(
#            EC.presence_of_element_located((By.ID, "search-input"))
#        )
#        search_input.send_keys("Hello, Selenium on iOS!")
#        
#        search_button = driver.find_element(By.ID, "search-button")
#        search_button.click()
#        
#        # Wait for search results
#        WebDriverWait(driver, 10).until(
#            EC.presence_of_element_located((By.CLASS_NAME, "search-results"))
#        )
#        
#        # Get search result titles
#        result_elements = driver.find_elements(By.CSS_SELECTOR, ".search-result-title")
#        for element in result_elements:
#            print(element.text)
#        
#        # Demonstrate error handling
#        try:
#            non_existent = driver.find_element(By.ID, "non-existent-element")
#        except NoSuchElementException:
#            print("Element not found, as expected")
#        
#
## Test implicit wait
#        driver.implicitly_wait(5)
#        try:
#            # This should wait up to 5 seconds before raising an exception
#            driver.find_element(By.ID, "element-that-takes-time-to-appear")
#        except NoSuchElementException:
#            print("Element did not appear within 5 seconds")
#
#
#        
#        # Execute JavaScript
#        title = driver.execute_script("return document.title;")
#        print(f"Page title: {title}")
#        
# #Test element visibility
#        button = driver.find_element(By.ID, "some-button")
#        if button.is_displayed():
#            button.click()
#        else:
#            print("Button is not visible")
#
#        
#        # Test getting attributes
#        link = driver.find_element(By.TAG_NAME, "a")
#        href = link.get_attribute("href")
#        print(f"Link href: {href}")
#        
#    except Exception as e:
#        print(f"An error occurred: {str(e)}")
#    finally:
#        driver.quit()
#

# Usage example

