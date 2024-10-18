from inspect import signature
from selenium.webdriver.common.options import ArgOptions
from selenium.webdriver import ChromeOptions, FirefoxOptions, EdgeOptions, IeOptions, WebKitGTKOptions, iOS
from selenium.webdriver import Chrome, Firefox, Edge, Ie, WebKitGTK, Safari
from selenium.webdriver.safari.options import Options as SafariOptions
from .utils import Config, BrowserType
from .action_executor import ActionExecutor


class Browser:
	"""Abstraction for all browser drivers"""

	"""Equivalences between browser type and driver and options"""
	EQUVALENCES = equivalences = {
		BrowserType.CHROME.value: [ChromeOptions, Chrome],
		BrowserType.FIREFOX.value: [FirefoxOptions, Firefox],
		BrowserType.EDGE.value: [EdgeOptions, Edge],
		BrowserType.IE.value: [IeOptions, Ie],
		BrowserType.SAFARI.value: [SafariOptions, WebKitGTK],
		BrowserType.WEBKITGTK.value: [WebKitGTKOptions, WebKitGTK]
	}

	def __init__(self, config: dict) -> None:
		self._config = Config(config)
		self._load_browser_props()
		self._action_executor = ActionExecutor(self._driver, self._config)

	@property
	def config(self) -> Config:
		return self._config

	@property
	def driver(self) -> ArgOptions | Chrome | Firefox | Edge | Ie | WebKitGTK | Safari:
		return self._driver

	def run(self) -> None:
		"""Init the action executor to interact with the browser"""
		self._action_executor.run()

	def _load_browser_props(self):
		"""Loads browser driver instance and options"""
		if self._config.get('general.browser.type') not in self.EQUVALENCES:
			raise Exception('Browser type not supported')
		else:
			options_class, driver_class = self.EQUVALENCES[self._config.get('general.browser.type')]
			self._options = self._create_options(options_class)
			self._driver = driver_class(self._config.get('general.browser.driver'), options=self._options)

	def _create_options(self, options_class):
		"""Creates the options instance for the browser and loads the options"""
		options = options_class()
		for opt_key, opt_value in self._config.get('general.browser.options', {}).items():
			if hasattr(options_class, opt_key):
				if callable(getattr(options_class, opt_key)):
					self._load_browser_method(options, opt_key, opt_value)
				else:
					setattr(options, opt_key, opt_value)
		return options

	def _load_browser_method(self, options, opt_key, opt_value) -> None:
		"""Loads the options method with the given arguments"""
		if isinstance(opt_value, dict):
			getattr(options, opt_key)(**opt_value)
		elif isinstance(opt_value, list):
			if (len(signature(getattr(options, opt_key)).parameters) > 1):
				getattr(options, opt_key)(*opt_value)
			else:
				for value in opt_value:
					getattr(options, opt_key)(value)
		else:
			getattr(options, opt_key)(opt_value)
