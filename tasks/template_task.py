import logging

from ciscoconfparse import CiscoConfParse
from jinja2.nodes import Template

from rules.template_rule import TemplateRule
from tasks.tester_task import TestTask

logger = logging.getLogger(__name__)


class DeviceRuleErrorNoMatches(Exception):
    pass


class TemplateTask(TestTask):
    def __init__(self, device_list, device_class_name=None, username=None, password=None, rules=None, rule_objs=None, timeout=60,
                 optional_args=None):

        self._objects = {}
        self._rule_templates = {}
        self._generated_templates = {}
        super().__init__(device_list, device_class_name=device_class_name, username=username, password=password, rules=rules, rule_objs=rule_objs, timeout=timeout,
                 optional_args=optional_args)

    @property
    def objects(self):
        return self._objects

    @property
    def generated_configs(self):
        return self._generated_templates

    def _load_device_rules(self, rules, rule_objs):
        super()._load_device_rules(rules, rule_objs)
        self._determine_templates()

    def run_rule(self, device, nugget=None, modify_config=False, save_objects=True):
        """

        :param nugget: integer
        :return:
        """
        yield from super().run_rule(device, nugget=None, modify_config=modify_config, save_objects=save_objects)

    def _determine_templates(self):
        for name, rule in self.loaded_rules.items():
            if hasattr(rule, 'template'):
                self._rule_templates[name] = rule.template
            else:
                self._rule_templates[name] = ""

    def generate_config_template(self, rule):
        if rule not in self.matches:
            raise DeviceRuleErrorNoMatches("Rule {} has not yet been checked for a match".format(rule))
        if self.matches[rule]:
            return self.loaded_rules[rule].exception, self.loaded_rules[rule].generate_config()

    def generate_all_device_configs(self, device, nugget=None):
        loaded_rules = {}
        if nugget and nugget not in self._generated_templates[device]:
            loaded_rules[nugget] = self.loaded_rules[nugget]
        else:
            loaded_rules = self.loaded_rules
        if not self.matches:
            raise DeviceRuleErrorNoMatches("Must Check for Matches before generating configurations")
        self.config = ''
        self._generated_templates[device] = {}
        for rule, rule_obj in loaded_rules.items():
            self.logger.debug("Running rule {} for device {} with objects {}".format(rule, device, self._objects[device]))
            if isinstance(rule_obj, TemplateRule):
                if self.matches[device][rule] and self.matches[device][rule] != "unknown":
                    logger.debug("generate_all_configs: rule: {}".format(rule_obj.exception))
                    self._generated_templates[device][rule] = "!*** {} ***\n{}\n\n".format(rule_obj.exception, rule_obj.generate_config(self._objects[device]))
                elif self.matches[device][rule] and self.matches[device][rule] == "unknown":
                    logger.critical("generate_all_configs: rule: {}, **ANALYSIS FAILED**".format(rule_obj.exception))
                    self._generated_templates[device][rule] = "!*** {} ***\n{}\nTemplate: {}\n\n".format(rule_obj.exception, "**ANALYSIS FAILED**, Configuration Must Be Generated Manually", rule_obj.template)
                else:
                    continue
        #self._generated_templates[device] = self.config
        logger.debug("generate_all_configs for device {}: self.config: {}".format(device, self._generated_templates[device]))

    def generate_all_configs(self):
        for device in self.device_list:
            self.generate_all_device_configs(device)


