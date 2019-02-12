import logging

logger = logging.getLogger('generic')

class GenericFunction:
    def __init__(self, name, func):
        self.name = name
        self.func = func
        self._command_list = []

    @property
    def command_list(self):
        return self._command_list

    @command_list.setter
    def command_list(self, command_list):
        logger.debug("generic: set_cli: cmds: {}".format(command_list))
        if isinstance(command_list, str):
            command_list = [command_list]
        self._command_list = command_list