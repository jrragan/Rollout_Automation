import abc
import importlib
import inspect
import logging
from collections import OrderedDict

from napalm.base import ModuleImportError

logger = logging.getLogger(__name__)


class abs_task(metaclass=abc.ABCMeta):
    def __init__(self, device_list, device_class_name=None, username=None, password=None, rules=None, rule_objs=None, timeout=60,
                 optional_args=None):
        """

        :param device_list: list
        :param device_class_name: str
        :param username: str
        :param password: str
        :param rules: list
        :param rule_objs: dict
        :param timeout: int
        :param optional_args: dict
        """
        self.logger = logging.getLogger("abs_task.abs_task")
        self.device_list = device_list
        self.logger.debug("determining driver for {}".format(device_class_name))
        if device_class_name:
            self.device_class = self._get_device_driver(device_class_name)
        else:
            self.device_class = device_class_name
        self.username = username
        self.password = password
        self.timeout = timeout
        self._skip_config = False
        self._skip_facts = False
        self._skip_commands = False
        self.optional_args = optional_args
        self._running_config = {}
        self._device_facts = {}
        self._cli_command_list = set([])
        self._get_method_list = set([])
        self._cli_commands = {}
        self._get_methods = {}
        self._confparsed_config = {}
        self._matches = {}
        self._objects = {}

        self.logger.debug("Rules: {} - Rule Objects: {}".format(rules, rule_objs))
        if rules is not None and rule_objs is not None:
            self.logger.debug("Loading Rules")
            self.set_device_rules(rules, rule_objs)

    @property
    def matches(self):
        return self._matches

    @property
    def running_config(self):
        return self._running_config

    @property
    def cli_commands(self):
        return self._cli_commands

    @property
    def device_facts(self):
        return self._device_facts

    @property
    def get_methods_results(self):
        return self._get_methods

    def get_device_matches(self, device):
        return self._matches[device]

    def get_rule_name(self, nugget):
        return self.loaded_rules[nugget].exception

    def _load_device_rules(self, rules, rule_objs):
        """

        :param rules: list of rule ids to load
        :param rule_objs: is a dictionary containing rule objects
        The rule ids loaded is an intersection of the all_rules dictionary and the device_nuggets list
        :return: None

        populates the self.matches attribute
        """
        self.logger.debug("_load_device_rules: rules {}, rule_objs ()".format(rules, rule_objs))
        self.loaded_rules = {}
        if not isinstance(rules, list):
            rules = [rules]
        self.logger.debug("Loading Rules: {}".format(rules))
        self.loaded_rules = OrderedDict(
            [(rule, rule_obj) for rule, rule_obj in rule_objs.items() if rule in rules])
        self.logger.debug("_load_device_rules: self.loaded_rules: {}".format(self.loaded_rules))

    @abc.abstractmethod
    def set_device_rules(self, rules, rule_objs):
        pass

    def _determine_cli_command_list(self):
        self.logger.debug("_determine_cli_command_list")
        self.logger.debug("original cli_command_list: {}".format(self._cli_command_list))
        for name, rule in self.loaded_rules.items():
            self.logger.debug("determing command list for {} - {}".format(name, rule))
            if rule.need_cli:
                self._cli_command_list = self._cli_command_list | rule.cli_commands

    def _determine_get_method_list(self):
        self.logger.debug("_determine_get_method_list")
        self.logger.debug("original get_method_list: {}".format(self._get_method_list))
        for name, rule in self.loaded_rules.items():
            self.logger.debug("determining get list for {} - {}".format(name, rule))
            if rule.need_get:
                self._get_method_list = self._get_method_list | rule._get_list

    def _get_device_driver(self, device_class_name):
        module_name = device_class_name.lower()
        self.logger.debug("module name should be {}".format(module_name))
        class_name = ["{}NapalmWrapper".format(device_class_name.title()), "{}Wrapper".format(device_class_name.title())]
        try:
            module = importlib.import_module("wrappers.{}".format(module_name))
        except ImportError as e:
            self.logger.critical("No module names {} found".format(module_name))
            raise e

        logger.debug("Looking for driver from module {}".format(module_name))
        for name, obj in inspect.getmembers(module):
            self.logger.debug("Inspecting {} and {}".format(name, obj))
            if inspect.isclass(obj) and name in class_name:
                self.logger.debug("Found driver {} - {}".format(name, obj))
                return obj

            # looks like you don't have any Driver class in your module...
        raise ModuleImportError(
            'No wrapper matching {} found'.format(class_name))

    @abc.abstractmethod
    def run_all_rules(self):
        pass

