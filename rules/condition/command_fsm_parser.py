import logging
from io import StringIO

import textfsm

from configuration.helpers import json_xpath
from rules.condition.abs_cond import AbsCondition

logger = logging.getLogger('command_fsm_parser')


class CmdFsmParse(AbsCondition):
    def __init__(self, name, cmdlist):
        super().__init__(name)
        self.parselist = cmdlist  # list of tuples
        self.need_cli = True

        logger.debug("CmdFsmParse: __init__: cmdlist: {}".format(cmdlist))
        self._command_list = self._get_commands()
        logger.debug("_command_list: {}".format(self._command_list))

    def _get_commands(self):
        return [cmd for cmd, _, _ in self.parselist]

    @property
    def command_list(self):
        return self._command_list

    @command_list.setter
    def command_list(self, cmd):
        pass

    def __str__(self):
        line = "CmdFsmParse: name: {}, parselist: {}".format(self.name, self.parselist)
        return line

    def run(self, cli_commands):
        logger.debug("Received cli commands dictionary: {}".format(cli_commands))
        parseresults = {}
        passed = True

        for cmdr, template, json_path in self.parselist:
            try:
                parseresult = cli_commands[cmdr]
            except KeyError as err:
                logger.critical("Missing command output for {}. Aborting.".format(cmdr))
                raise
            logger.debug("command_fsm_parser: cmdr: {}: result {}".format(cmdr, parseresult))
            logger.debug(
                "command_fsm_parser: - Testing {} - {}".format(cmdr, template))

            if isinstance(template, str):
                template_file = open(template)
            elif not isinstance(template, StringIO):
                logger.critical("template must be a filename or a StringIO object. aborting.")
                raise TypeError("template must be a filename or a StringIO object")
            else:
                template_file = template

            re_table = textfsm.TextFSM(template_file)
            fsm_results = re_table.ParseText(parseresult)
            logger.debug("raw text fsm results: {}".format(fsm_results))

            keys = [s for s in re_table.header]
            logger.debug("keys for text fsm output: {}".format(keys))

            parseresults[cmdr] = {'result' : {}}
            for row_num, row in enumerate(fsm_results):
                temp_dict = {}
                for index, value in enumerate(row):
                    temp_dict[keys[index]] = value
                parseresults[cmdr]['result']['row{}'.format(row_num + 1)] = temp_dict
            passed = passed and bool(parseresults[cmdr])

            if json_path:
                parseresults[cmdr] = json_xpath(parseresults[cmdr], json_path)

        return str(passed), parseresults
