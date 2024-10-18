"""Configuration loader and action executor for Selenium"""

__version__ = "0.3"

from .action_executor import ActionExecutor
from .utils import BrowserType, Config
from .custom_web_driver_handler import CustomWebDriverHandler
from .browser import Browser
