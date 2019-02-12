class ConfigureDevice:
    def __init__(self, name, config_file=False, snippet=None, file=None, replace=False):
        """

        :param name: str
        :param config_file: bool - True - config file, False - configuration snippet
        :param snippet: str - configuration snippet
        :param file: str - filename
        :param replace: bool - True - replace existing config, False, merge existing configuration

        Allowed combinations
        config_file=False, snippet=str, file=None, replace=False|True
        config_file=True, snippet=None, file=str, replace=False|True

        other combinations are not allowed
        """
        if config_file and snippet:
            raise AttributeError("If config_file is True, snippet must be None")
        if config_file and not file:
            raise AttributeError("If config_file is True, file must be a filename")
        if not config_file and not snippet:
            raise AttributeError("If config_file is False, configuration snippet must be included")
        if not config_file and file:
            raise AttributeError("If config_file is False, file must be None")
        if snippet and file:
            raise AttributeError("Both snippet and file cannot be set")

        self.name = name
        self.config_file = config_file
        self.snippet = snippet
        self.file = file
        self.replace = replace

