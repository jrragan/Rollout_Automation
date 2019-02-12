import abc


class AbsRule(metaclass=abc.ABCMeta):
    def __init__(self, name):
        self.name = name
        self.need_cli = False
        self.need_get = False

    @abc.abstractmethod
    def run(self, parse):
        """required method"""