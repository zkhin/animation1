import re, json

from .config_validator import ConfigValidator
from .browser_type import BrowserType


class Config:
	def __init__(self, raw_config: dict) -> None:
		ConfigValidator.validate(raw_config)
		self._raw_config = raw_config

	def variable_resolver(self, data: str | dict) -> str | dict:
		if not data:
			return data

		was_object = isinstance(data, dict) or isinstance(data, list)
		data = json.dumps(data) if was_object else data
		data = re.sub(
			r"\$\{(\w+)\}",
			lambda match: self._raw_config["general"]["variables"][match.group(1)] if match.group(1) in self._raw_config["general"]["variables"] else "",
			data
		)
		return json.loads(data) if was_object else data

	def get(self, key: str, default: any = None, variable_resolution: bool = True) -> any:
		default = default if not variable_resolution else self.variable_resolver(default)
		key = key if not variable_resolution else self.variable_resolver(key)
		buffer = self._raw_config if not variable_resolution else self.variable_resolver(self._raw_config)

		for key in key.split('.'):
			if key in buffer:
				buffer = buffer[key]
			else:
				return default

		return buffer

	def set(self, key: str, value: any, seed: any = None, calls: int = 0) -> any:
		seed = self._raw_config if calls == 0 and not seed else seed
		keys = key.split('.')
		current = keys[-1]

		if type(seed) == dict:
			if current in seed:
				seed[current] = value
			else:
				for local_key, local_value in seed.items():
					seed[local_key] = self.set('.'.join(keys[1:]), value, local_value, calls + 1)
					calls += 1
		else:
			if current:
				seed = value

		return seed
