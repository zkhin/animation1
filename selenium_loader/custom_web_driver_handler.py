import os, re, pathlib, time

from selenium.webdriver.remote.webelement import WebElement


class CustomWebDriverHandler:
	@classmethod
	def submit_with_download(cls, element: WebElement, timeout: int, download_dir: str, actuator: str = 'submit') -> set[str]:
		getattr(element, actuator)()

		download_dir = pathlib.Path(download_dir).absolute()
		original_files = set(os.listdir(download_dir))
		to_ignore = len(re.findall(".crdownload", "|".join(original_files)))
		current_files = set()
		download_complete = False
		seconds = 0

		while not download_complete and seconds < timeout:
			time.sleep(1)
			seconds += 1
			current_files = set(os.listdir(download_dir))
			download_complete = not (len(re.findall(".crdownload", "|".join(current_files))) - to_ignore)

		return ["{}/{}".format(download_dir, file) for file in (current_files - original_files)]
