import logging
from collections import OrderedDict

from ciscoconfparse import CiscoConfParse

from device.device import Device
from tasks.abs_task import abs_task

logger = logging.getLogger(__name__)


class TestTask(abs_task):

    def set_device_rules(self, rules, rule_objs):
        """
        Manually set the rules to evaluate for this device

        :param rules: a list of the rule IDs for this device
        :param rule_objs: a dictionary of rule objects
        :return: None

        sets self.loaded_rules: a dictionary of rule objects

        {545551: <np_get_bp.Rule object at 0x000002690D828A58>, 549320: <np_get_bp.Rule object at 0x000002690D82DDA0>,
        547314: <np_get_bp.Rule object at 0x000002690E233518>, 547863: <np_get_bp.Rule object at 0x000002690E223FD0>,
        544840: <np_get_bp.Rule object at 0x000002690D82D400>, 544986: <np_get_bp.Rule object at 0x000002690D8284A8>,
        547935: <np_get_bp.Rule object at 0x000002690D82D898>, 545176: <np_get_bp.Rule object at 0x000002690D828EB8>,
        549549: <np_get_bp.Rule object at 0x000002690E2339E8>, 547182: <np_get_bp.Rule object at 0x000002690E233F98>,
        550200: <np_get_bp.Rule object at 0x000002690E22F2B0>}

        """
        self.logger.debug("set_device_rules: rules: {}".format(rules))
        self._load_device_rules(rules, rule_objs=rule_objs)
        self._determine_cli_command_list()
        self._determine_get_method_list()

    def run_rule(self, device, nugget=None, modify_config=False, save_objects=False):
        """

        :param nugget: integer
        :return:
        """
        loaded_rules = {}
        if nugget and nugget not in self.matches[device]:
            loaded_rules[nugget] = self.loaded_rules[nugget]
        else:
            loaded_rules = self.loaded_rules
        self.logger.debug("Running loaded rules: {}".format(loaded_rules))
        self._confparsed_config[device] = CiscoConfParse(self.running_config[device].splitlines())
        self.logger.debug("_confparsed_config: {}".format(self._confparsed_config))
        self._matches[device] = {}
        self._objects[device] = {}
        for rule, rule_obj in loaded_rules.items():
            logger.debug("Running rule {} - {} for device {}".format(rule, rule_obj, device))
            if not save_objects:
                if rule_obj.need_cli:
                    logger.debug(
                        "Don't save objects. Need cli output to run rule: {}".format(self._cli_commands[device]))
                    self._matches[device][rule], _, pcfg = rule_obj.confirm_match(self._confparsed_config[device],
                                                                                  cli_commands=self._cli_commands[
                                                                                      device],
                                                                                  hard_dict=self.device_facts[device],
                                                                                  get_methods_output=
                                                                                  self.get_methods_results[device],
                                                                                  modify_config=modify_config)
                else:
                    logger.debug("Don't save objects. Does not need cli output to run rule.")
                    self._matches[device][rule], _, pcfg = rule_obj.confirm_match(self._confparsed_config[device],
                                                                                  hard_dict=self.device_facts[device],
                                                                                  get_methods_output=
                                                                                  self.get_methods_results[device],
                                                                                  modify_config=modify_config)
            else:
                if rule_obj.need_cli:
                    logger.debug(
                        "Save objects. Need cli output to run rule: {}".format(self._cli_commands[device]))
                    self.matches[device][rule], obj, pcfg = rule_obj.confirm_match(
                        self._confparsed_config[device],
                        cli_commands=self._cli_commands[device],
                        hard_dict=self.device_facts[device],
                        get_methods_output=self.get_methods_results[device],
                        modify_config=modify_config)
                else:
                    logger.debug("Save objects. Does not need cli output to run rule.")
                    self.matches[device][rule], obj, pcfg = rule_obj.confirm_match(
                        self._confparsed_config[device],
                        hard_dict=self.device_facts[device],
                        get_methods_output=self.get_methods_results[device],
                        modify_config=modify_config)
                self._objects[device].update(obj)
            if modify_config:
                self._confparsed_config[device] = pcfg
            yield self.get_rule_name(rule), self.matches[device][rule]

    def run_all_rules(self, modify_config=False, skip_info=False,
                      skip_config=False, skip_facts=False, skip_commands=False, skip_methods=False, configs=None,
                      commands=None, facts=None, methods=None):
        if configs and not isinstance(configs, dict):
            raise AttributeError("configs must be a dictionary")
        if commands and not isinstance(commands, dict):
            raise AttributeError("commands must be a dictionary")
        if facts and not isinstance(configs, dict):
            raise AttributeError("facts must be a dictionary")
        self._skip_info = skip_info
        self._skip_config = skip_config
        self._skip_facts = skip_facts
        self._skip_commands = skip_commands
        self._skip_methods = skip_methods
        if configs:
            self._skip_config = True
            self._running_config = configs
        if commands:
            self._skip_commands = True
            self._cli_commands = commands
        if facts:
            self._skip_facts = True
            self._device_facts = facts
        if methods:
            self._skip_methods = True
            self._get_methods = {}
        self.get_device_info()

        self.logger.debug("Running all rules for loaded rules {}".format(self.loaded_rules))
        for device in self.device_list:
            self.logger.debug("Running all rules for {}".format(device))
            self.run_all_device_rules(device, modify_config=modify_config)
        return self.matches

    def run_all_device_rules(self, device, modify_config=False):
        """

        Analyzes all of the loaded rules for the device. For each loaded rule object, it calls the confirm_match
        method.

        :return: self.matches, dict. Example:
        """
        for _ in self.run_rule(device, modify_config=modify_config):
            continue
        self.logger.debug("confirm_all_matches: self.matches: {}".format(self.matches))

    def get_device_info(self):
        for device_name in self.device_list:
            self.logger.info("Getting info for device {}".format(device_name))
            self.logger.debug("Entering context manager for {}".format(self.device_class))
            if not self._skip_info:
                with Device(device_name, self.device_class, self.username, self.password, timeout=self.timeout,
                            optional_args=self.optional_args) as device:
                    if not self._skip_config:
                        self.logger.debug("Getting config for device {}".format(device_name))
                        device.get_config()
                        self._running_config[device_name] = device.running_config
                        self.logger.debug("Received config")
                    elif device_name not in self._running_config:
                        self._running_config[device_name] = ""
                    if not self._skip_facts:
                        self._device_facts[device_name] = device.get_facts()
                    elif device_name not in self._device_facts:
                        self._device_facts[device_name] = {}
                    self.logger.debug("command list for {}: {}".format(device_name, self._cli_command_list))
                    if not self._skip_commands and self._cli_command_list:
                        self.logger.debug("Sending commands {} to {}".format(self._cli_command_list, device_name))
                        device.run_cli_command_list(self._cli_command_list)
                        self._cli_commands[device_name] = device.cli_command_output
                        logger.debug(
                            "_cli_commands for device {} : {}".format(device_name, self._cli_commands[device_name]))
                    elif device_name not in self._cli_commands:
                        self._cli_commands[device_name] = {}
                    if not self._skip_methods and self._get_method_list:
                        self._get_methods[device_name] = {}
                        for method in self._get_method_list:
                            self.logger.debug("Running napalm method {} to {}".format(method, device_name))
                            result = eval(f"device.{method}()")
                            self._get_methods[device_name][method] = result
                            logger.debug("results for method {} on device {} : {}".format(method, device_name,
                                                                                          self._get_methods[device_name][
                                                                                              method]))
                        logger.debug("final methods dictionary: {}".format(self._get_methods[device_name]))
                    elif device_name not in self._get_methods:
                        self._get_methods[device_name] = {}
            else:
                if device_name not in self._running_config:
                    self._running_config[device_name] = ""
                if device_name not in self._device_facts:
                    self._device_facts[device_name] = {}
                if device_name not in self._cli_commands:
                    self._cli_commands[device_name] = {}
                if device_name not in self._get_methods:
                    self._get_methods[device_name] = {}