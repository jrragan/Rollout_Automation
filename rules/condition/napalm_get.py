import logging
from abc import ABC

from configuration.helpers import json_xpath
from rules.condition.abs_cond import AbsCondition

logger = logging.getLogger('napalm_get')


class NapalmGet(AbsCondition, ABC):
    def __init__(self, name, command):
        super().__init__(name)
        self._command = command   #list of tuples [(get_command, json_path)]
        self.need_get = True
        self._get_list = ["get_{}".format(com) for com, path in self._command]

    def __str__(self):
        line = "NapalmGet: name: {}: commands: {}".format(self.name, self._command)
        return line

    @property
    def get_list(self):
        return self._get_list

    @get_list.setter
    def get_list(self, cmd):
        pass

    def run(self, get_method_output):
        logger.debug("Received get methods dictionary: {}".format(get_method_output))
        parseresults = {}
        passed = True

        for getr, path in self._command:
            cmdr = "get_{}".format(getr)
            try:
                parseresults[cmdr] = get_method_output[cmdr]
            except KeyError as err:
                logger.critical("Missing command output for {}. Aborting.".format(cmdr))
                raise
            logger.debug("get_method_output: cmdr: {}: result {}".format(cmdr, parseresults[cmdr]))
            passed = passed and bool(parseresults[cmdr])

            if path:
                parseresults[cmdr] = json_xpath(parseresults[cmdr], path)

        return str(passed), parseresults



