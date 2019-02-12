import sys
import traceback

from napalm.base.exceptions import MergeConfigException, ReplaceConfigException

from device.device import Device
from rules.deploy.config_obj import Configuration
from rules.rule import Rule
from rules.template_rule import TemplateRule
from tasks.abs_task import abs_task
from tasks.template_task import TemplateTask
from tasks.tester_task import TestTask


class ConfigTask(TemplateTask):
    """
    A configuration task can:
    1. Run tests and determine whether to do configs based on the outcome of those tests. If tests are configured in
       the task, subsequent configurations will only be deployed if the tests passed.
    2. Can generate per-device/per-rule templates, similar to the template task or use rule generated objects to
        generate a template or templates - either a single template or per-device templates
    3. Simple push of config
    4. Use a separate function to generate config

    A config can be provided as a file or a string
    A config push can be either a replace or a merge
    """

    def __init__(self, device_list, device_class_name=None, username=None, password=None,
                 rules=None,
                 rule_objs=None,
                 template=None,
                 config=None,
                 filename=None,

                 template_type='single',
                 template_deploy='merge',
                 prompt=False,
                 timeout=60,
                 optional_args=None):

        super().__init__(device_list, device_class_name=device_class_name, username=username, password=password, rules=rules, rule_objs=rule_objs,
                         timeout=timeout,
                         optional_args=optional_args)

        self._prompt = prompt

    def set_device_rules(self, rules, rule_objs):
        """

        :param rules:
        :param rule_objs:
        :return:
        """
        self.test_rules = False
        self.logger.debug("set_device_rules: rules: {}".format(rules))
        self._load_device_rules(rules, rule_objs=rule_objs)
        self._determine_if_test_rules()
        if self.test_rules:
            self._determine_cli_command_list()

    def _determine_if_test_rules(self):
        self.logger.debug("_determine_if_test_rules")
        self.logger.debug("original rule_list: {}".format(self.loaded_rules))
        for name, rule in self.loaded_rules.items():
            self.logger.debug("determing if rule {} - {} is a test rule".format(name, rule))
            if not isinstance(rule, TemplateRule) and isinstance(rule, Rule):
                self.test_rules = True
                break

    def run_all_device_rules(self, device, modify_config=False):
        """

        Analyzes all of the loaded rules for the device. For each loaded rule object, it calls the confirm_match
        method.

        :return: self.matches, dict. Example:
        """
        for rule, rule_obj in self.loaded_rules.items():
            if isinstance(rule, TemplateRule) or isinstance(rule, Rule):
                self.run_rule(device, nugget=rule, modify_config=modify_config)
                if isinstance(rule, TemplateRule):
                    self.generate_all_device_configs(device, nugget=rule)
                else:
                    self.test_rules = True
            elif isinstance(rule, Configuration):
                self._push_config(device, rule)


        self.logger.debug("confirm_all_matches: self.matches: {}".format(self.matches))

    def _push_config(self, device_name, rule):
        self.logger.debug("Loading {} candidate ...".format(rule.deploy))
        with Device(device_name, self.device_class, self.username, self.password, timeout=self.timeout,
                    optional_args=self.optional_args) as device:
            device.get_config()
            self.running_config[device_name] = device.running_config
            try:
                f"device.load_{rule.deploy}_candidate(filename=rule.filename, config=rule.config)"
            except (MergeConfigException, ReplaceConfigException) as err:
                exc_type, exc_value, exc_traceback = sys.exc_info()
                stacktrace = traceback.extract_tb(exc_traceback)
                self.logger.critical("_push_config: fatal error: {}, In loading merge/replace configuration: {} - {}".format(err, exc_type, exc_value))
                self.logger.debug(sys.exc_info())
                self.logger.debug(stacktrace)
                device.close()
                raise
            except:
                exc_type, exc_value, exc_traceback = sys.exc_info()
                stacktrace = traceback.extract_tb(exc_traceback)
                self.logger.critical(
                    "_push_config: unknown error in loading merge/replace configuration: {} - {}. AAGGGHHHH! We're all going to die!".format(exc_type, exc_value))
                self.logger.debug(sys.exc_info())
                self.logger.debug(stacktrace)
                device.close()
                raise
            diffs = device.compare_config()
            self.logger.warning("Configuration Diffs: {}".format(diffs))
            choice = ''
            if self._prompt:
                # You can commit or discard the candidate changes.
                while choice not in 'yN':
                    choice = input("\nWould you like to commit these changes? [yN]: ")
            if not self._prompt or choice == 'y':
                print('Committing ...')
                self.logger.debug("Committing...")
                try:
                    device.commit_config()
                except (MergeConfigException, ReplaceConfigException) as err:
                    exc_type, exc_value, exc_traceback = sys.exc_info()
                    stacktrace = traceback.extract_tb(exc_traceback)
                    self.logger.critical(
                        "_push_config: fatal error: {}, In committing merge/replace configuration: {} - {}".format(err,
                                                                                                           exc_type, exc_value))
                    self.logger.debug(sys.exc_info())
                    self.logger.debug(stacktrace)
                    device.close()
                    raise
                except:
                    exc_type, exc_value, exc_traceback = sys.exc_info()
                    stacktrace = traceback.extract_tb(exc_traceback)
                    self.logger.critical(
                        "_push_config: unknown error in committing merge/replace configuration: {} {}. AAGGGHHHH! We're all going to die!".format(
                            exc_type, exc_value))
                    self.logger.debug(sys.exc_info())
                    self.logger.debug(stacktrace)
                    device.close()
                    raise
            elif self._prompt and choice == 'N':
                print('Discarding ...')
                self.logger.debug("Discarding...")
                device.discard_config()
            else:
                self.logger.critical("Something horrible has happened in pushing the configuration to device {} and I cannot continue.".format(device_name))
                self.logger.critical("You will need to manually check the device and manually correct if necessary.")
                raise RuntimeError("Error pushing configuration. Manually check the device and manually correct the configuration.")




