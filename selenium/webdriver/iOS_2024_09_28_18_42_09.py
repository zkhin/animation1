import ui
import time
import objc_util

from objc_util import ObjCClass, ObjCInstance, on_main_thread
from selenium.webdriver.remote.webdriver import WebDriver as RemoteWebDriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException, TimeoutException, WebDriverException, ElementNotVisibleException, ElementNotInteractableException

# ObjC bridge to WebKit
WKWebView = ObjCClass('WKWebView')
WKWebViewConfiguration = ObjCClass('WKWebViewConfiguration')
NSURLRequest = ObjCClass('NSURLRequest')
NSURL = ObjCClass('NSURL')

class iOSWebDriver(RemoteWebDriver):
    def __init__(self, timeout=10):
        self._timeout = timeout
        self.view = None
        self.webview = None
        self.create_webview()

        # Dummy URL for the executor (Selenium expects this)
        self.command_executor = 'http://localhost:0'
        self.w3c_compliant = True

    @on_main_thread
    def create_webview(self):
        try:
            screen_width, screen_height = ui.get_screen_size().width, ui.get_screen_size().height
            frame = (0, 0, screen_width, screen_height)
            self.view = ui.View(frame=frame)

            config = WKWebViewConfiguration.new()
            self.webview = WKWebView.alloc().initWithFrame_configuration_(((0, 0), (frame[2], frame[3])), config)

            ObjCInstance(self.view).addSubview_(self.webview)

            # Present the view
            def present_view():
                self.view.present('panel', hide_title_bar=True)

            present_view()
            print("WebView presented.")
        except Exception as e:
            print(f"Error creating WebView: {str(e)}")
            raise

    def get(self, url):
        self._execute_webkit(lambda: self._load_url(url))
        self._wait_for_page_load()

    @on_main_thread
    def _load_url(self, url):
        request = NSURLRequest.requestWithURL_(NSURL.URLWithString_(url))
        self.webview.loadRequest_(request)

    def _wait_for_page_load(self, timeout=None):
        if timeout is None:
            timeout = self._timeout
        end_time = time.time() + timeout
        while time.time() < end_time:
            if not self._execute_webkit(lambda: self.webview.loading()):
                return
            time.sleep(0.1)
        raise TimeoutException("Page load timeout")


    def find_element(self, by=By.ID, value=None):
        return self._find_element(by, value)

    def find_elements(self, by=By.ID, value=None):
        return self._find_elements(by, value)

    def _find_element(self, by, value):
        js_locator = self._get_js_locator(by, value)
        return self._execute_webkit(lambda: self._find_element_by_js(js_locator))

    def _find_elements(self, by, value):
        js_locator = self._get_js_locator(by, value, multiple=True)
        return self._execute_webkit(lambda: self._find_elements_by_js(js_locator))

    def _get_js_locator(self, by, value, multiple=True):
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
            return iOSWebElement(self, result)
        raise NoSuchElementException(f"No element found with JavaScript locator: {js}")

    @on_main_thread
    def _find_elements_by_js(self, js):
        results = self.webview.evaluateJavaScript_completionHandler_(js, None)
        return [iOSWebElement(self, result) for result in results] if results else []

    def execute_script(self, script, *args):
        return self._execute_webkit(lambda: self._execute_script(script, *args))

    @on_main_thread
    def _execute_script(self, script, *args):
        for i, arg in enumerate(args):
            if isinstance(arg, iOSWebElement):
                script = script.replace(f"arguments[{i}]", f'document.getElementById("{arg.id}")')
            else:
                script = script.replace(f"arguments[{i}]", repr(arg))
        return self.webview.evaluateJavaScript_completionHandler_(script, None)
    def execute_script(self, script, *args):
        return self._execute_webkit(lambda: self._execute_script(script, *args))
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
    @on_main_thread
    def _execute_script(self, script, *args):
        for i, arg in enumerate(args):
            if isinstance(arg, iOSWebElement):
                script = script.replace(f"arguments[{i}]", f'document.getElementById("{arg.id}")')
            else:
                script = script.replace(f"arguments[{i}]", repr(arg))
        return self.webview.evaluateJavaScript_completionHandler_(script, None)

    def implicitly_wait(self, time_to_wait):
        self._timeout = time_to_wait

    def quit(self):
        self._execute_webkit(lambda: self.view.close())

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

class iOSWebElement:
    def __init__(self, parent, element_id):
        self.parent = parent
        self.id = element_id

    def click(self):
        self.parent.execute_script(f'document.getElementById("{self.id}").click();')

    def send_keys(self, text):
        self.parent.execute_script(f'document.getElementById("{self.id}").value = "{text}";')

    def is_displayed(self):
        return self.parent.execute_script(f'return document.getElementById("{self.id}").offsetParent !== null;')

    def get_attribute(self, name):
        return self.parent.execute_script(f'return document.getElementById("{self.id}").getAttribute("{name}");')

    def get_text(self):
        return self.parent.execute_script(f'return document.getElementById("{self.id}").textContent;')

    def clear(self):
        self.parent.execute_script(f'document.getElementById("{self.id}").value = "";')

def install_ios_webdriver():
    try:
        from selenium import webdriver
        webdriver.iOSWebDriver = iOSWebDriver
        print("iOSWebDriver installed successfully.")
    except ImportError:
        print("Error: Selenium is not installed. Please install Selenium first.")
    except Exception as e:
        print(f"An error occurred while installing iOSWebDriver: {str(e)}")

# Example usage
if __name__ == "__main__":
    install_ios_webdriver()
    
    from selenium import webdriver
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC

    driver = webdriver.iOSWebDriver()
    driver.get("https://www.google.com")

    search_input = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.NAME, "q"))
    )
    search_input.send_keys("Pythonista Selenium WebDriver")

    search_button = driver.find_element(By.NAME, "btnK")
    search_button.click()

    WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.ID, "search"))
    )

    results = driver.find_elements(By.CSS_SELECTOR, ".LC20lb")
    for result in results:
        print(result.get_text())



    driver.get("https://www.example.com")
    
    # Wait for an element to load and interact with it
    search_box = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.NAME, "q"))
    )
    search_box.send_keys("Pythonista WebDriver")
    
    # Submit the form
    search_box.submit()
    
    # Wait for the search results to load
    WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.ID, "search-results"))
    )
    
    # Click on the first search result
    first_result = driver.find_element(By.CSS_SELECTOR, ".result-title")
    first_result.click()
    
    # Quit the driver
    driver.quit()
    driver.quit()
    
