import logging
import sys
import traceback

from rules.absrule import AbsRule

logger = logging.getLogger('get_config')

class GetRunConfigRule(AbsRule):
    def run(self, device):
        try:
            device.get_config(retrieve='running')
            return 'True', device.running_config
        except:
            exc_type, exc_value, exc_traceback = sys.exc_info()
            stacktrace = traceback.extract_tb(exc_traceback)
            logger.critical("Device: get_config: error retrieving configs")
            logger.debug(sys.exc_info())
            logger.debug(stacktrace)
            raise