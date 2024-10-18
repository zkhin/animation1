class ConfigValidator:
	MESSAGE_FORMAT = "\"{}\" should contains the following keys: {}."
	STRUCTURE = {
		"general": {"browser": ["type", "driver"], "variables": None},
		"steps": {
			"*.name": None,
			"*.actions": {
				"*.command": None,
				"*.parameters": None
			}
		}
	}

	@classmethod
	def throw_handler(cls, message: str, throw_exception: bool) -> bool:
		if throw_exception:
			raise ValueError(message)
		else:
			return False

	@classmethod
	def validate(cls, config: dict, structure: dict|list = None, key: str = "config", throw_exception: bool = True) -> bool:
		structure = structure if structure else cls.STRUCTURE
		buffer_str = structure if isinstance(structure, dict) else {structure[i]: None for i in range(len(structure))}
		buffer_str = {key.replace("*.", ""): value for key, value in buffer_str.items()}

		if not config or not all([key in config for key in buffer_str.keys()]):
			return cls.throw_handler(cls.MESSAGE_FORMAT.format(key, ", ".join(buffer_str.keys())), throw_exception)
		else:
			for key_str, value_str in buffer_str.items():
				if value_str:
					if isinstance(config[key_str], list):
						i = len(config[key_str])
						while i > 0:
							i -= 1
							if not cls.validate(config[key_str][i], value_str, "{}[{}]".format(key_str, i)):
								return cls.throw_handler(cls.MESSAGE_FORMAT.format("{}[{}]".format(key_str, i), ", ".join(value_str.keys())), throw_exception)
					else:
						if not cls.validate(config[key_str], value_str, key_str):
							return cls.throw_handler(cls.MESSAGE_FORMAT.format(key_str, ", ".join(value_str.keys())), throw_exception)
				else:
					continue
			return True
