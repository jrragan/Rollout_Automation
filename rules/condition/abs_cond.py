import abc


class AbsCondition(metaclass=abc.ABCMeta):
    def __init__(self, name):
        self.name = name
        self.need_cli = False
        self.need_get = False
        self._command_list = []
        self._get_list = []

    @abc.abstractmethod
    def __str__(self):
        """required method"""

    @abc.abstractmethod
    def run(self, parse):
        """required method"""