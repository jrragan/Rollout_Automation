import logging
import traceback
from collections import namedtuple

import sys

from configuration.helpers import update_config
from rules.condition.block_match import BlockMatch
from rules.condition.child_match import ChildMatch
from rules.condition.command_fsm_parser import CmdFsmParse
from rules.condition.compareos import CompareOS
from rules.condition.count import Count
from rules.condition.generic import GenericFunction
from rules.condition.match import Match
from rules.condition.napalm_get import NapalmGet
from rules.condition.parent_and_child_match import ParentChildMatch
from rules.condition.software_parsing_and_eval import parser
from rules.condition.command_parser import CmdParse

logger = logging.getLogger(__name__)


class CannotCompleteAnalysisError(Exception):
    pass


class Rule:

    def __init__(self, title):
        # self._token_map = {'&':'and', '|':'or', '!':'not', '(':'LPAR', ')':'RPAR'}
        # self._Token = namedtuple('Token', ['name', 'value'])
        self.exception = title
        self.need_cli = False
        self._cli_commands = set([])
        self.need_get = False
        self._get_list = set([])

    def set_confirm_match(self, *expr):
        """
        expr is a logical expression

        Examples:
        The following creates a rule to check for syslog servers
        logging_server_match = Match("logging_server", "global", (False, "^logging\s+server"))
        logging_server_rule = Rule("Logging to a syslog server not enabled ")
        logging_server_rule.set_confirm_match(logging_server_match)
        [Token(name='EXPR', value=<np_get_bp.Match object at 0x000002AB9A1A8400>)]

        The following creates a rule to check for multiple NTP servers
        NX_OS_Redundant_NTP_Servers_not_Configured_count = Count("NX_OS_Redundant_NTP_Servers_not_Configured", "global", (True, r"^ntp +server +\d+.\d+.\d+.\d+ +use-vrf +management", "< 2"))
        NX_OS_Redundant_NTP_Servers_not_Configured_rule = Rule('No redundant NTP server')
        NX_OS_Redundant_NTP_Servers_not_Configured_rule.set_confirm_match(NX_OS_Redundant_NTP_Servers_not_Configured_count)
        sets self.tokens to [Token(name='COUNT', value=<np_get_bp.Count object at 0x000001A9FA7CA438>)]

        The following creates a rule to check for copp profile
        default_vdc_match = Match("default_vdc", "global", "^vdc.*?id 1")
        copp_profile_match = Match("copp_profile", "global", (False, r"^copp\s+profile\s+(strict|dense)"))
        copp_profile_rule = Rule("Control Plane Policing is Disabled, or different then copp profile strict is used")
        copp_profile_rule.set_confirm_match(default_vdc_match, "&", copp_profile_match)
        sets self.tokens to [Token(name='EXPR', value=<np_get_bp.Match object at 0x000002AB9A1A8908>),
        Token(name='and', value='&'),
        Token(name='EXPR', value=<np_get_bp.Match object at 0x000002AB9A1A8A20>)]


        A more complex example that looks for loopguard on VPCs
        feature_vpc_match = Match("feature_vpc", "global", (True, r"^feature\s+vpc"))
        global_loopguard_match = Match("global_loopguard", "global", (True, r"^spanning-tree\s+loopguard\s+default"))
        global_no_loopguard_match = Match("global_no_loopguard", "global", (False, r"^spanning-tree\s+loopguard\s+default"))
        interface_vpc_no_loopguard_match = Match("interface_vpc_no_loopguard", r"interface port-channel", [(True, r"vpc\s+"), (False, r"no\s+spanning-tree\s+guard\s+loop")])
        interface_vpc_loopguard_match = Match("interface_vpc_loopguard", r"interface port-channel", [(True, r"vpc\s+"), (True, r"spanning-tree\s+guard\s+loop")])
        loopguard_no_vpc_ports_rule = Rule("Loopguard Enabled Globally with vPC and on vPC Ports")
        loopguard_no_vpc_ports_rule.set_confirm_match(feature_vpc_match, "&",
                                                  "(",
                                                  global_loopguard_match,
                                                  "&",
                                                  interface_vpc_no_loopguard_match,
                                                  ")",
                                                  "|",
                                                  "(",
                                                  global_no_loopguard_match,
                                                  "&",
                                                  interface_vpc_loopguard_match,
                                                  ")"
                                                  )
        sets self.tokens to [Token(name='EXPR', value=<np_get_bp.Match object at 0x000002AB9A649E48>),
        Token(name='and', value='&'), Token(name='(', value='('),
        Token(name='EXPR', value=<np_get_bp.Match object at 0x000002AB9A649EB8>),
        Token(name='and', value='&'),
        Token(name='EXPR', value=<np_get_bp.Match object at 0x000002AB9A649E80>),
        Token(name=')', value=')'),
        Token(name='or', value='|'),
        Token(name='(', value='('),
        Token(name='EXPR', value=<np_get_bp.Match object at 0x000002AB9A649EF0>),
        Token(name='and', value='&'),
        Token(name='EXPR', value=<np_get_bp.Match object at 0x000002AB9A649F28>),
        Token(name=')', value=')')]

        This example checks that the loopback interfaces have host addresses
        loopback_host_address_match = Match("loopback_host_address", r"interface [lL]oopback", ["ip address", (False, r"\s+ip address\s+[\d\.]+(/32|\s+255.255.255.255)")])
        loopback_host_address_rule = Rule("Loopback Interface Not Configured With Host Address")
        loopback_host_address_rule.set_confirm_match(loopback_host_address_match)
        sets self.tokens to [Token(name='EXPR', value=<np_get_bp.Match object at 0x000002E44C9941D0>)]

        This example checks that lacp is configured on portchannel links
        nxos_lacp_not_enabled_on_all_port_channels_match = Match("nxos_lacp_not_enabled_on_all_port_channels", r"^interface", [(True, r"^\s+channel-group\s+\d+"), (False, r"^\s+switchport\s+mode\s+fex-fabric"),
                                                                                                                           (True, r"^\s+channel-group\s+\d+$"), (True, r"^\s+channel-group\s+\d+mode\s+on")])
        nxos_port_channel_numbers_child_match = ChildMatch("nxos_port_channel_numbers", r"^interface Eth", r"^\s+channel-group\s+(\d+)")
        nxos_lacp_not_enabled_on_all_port_channels_rule = Rule("LACP Not Enabled On All Port-Channels")
        nxos_lacp_not_enabled_on_all_port_channels_rule.set_confirm_match(nxos_lacp_not_enabled_on_all_port_channels_match,
                                                                      "&",
                                                                      nxos_port_channel_numbers_child_match)

        :param expr: Can be a combination of Match, Count or Generic objects separated by one or more of the following
        &, |, !, ()
        :return: None

        sets the tokens attribute
        """
        logger.debug("set_confirm_match: expr {}, *expr {}".format(expr, *expr))
        self.tokens = self._tokenize(expr)
        self._check_for_cli()
        self._check_for_get()
        logger.debug("set_confirm_match: tokens {}".format(self.tokens))

    def _tokenize(self, expr):
        """
        Takes the expression defined with the set_confirm_match method and returns a list of tokens
        :param expr: as defined by set_confirm_match method
        :return: list of tokens
        """
        token_map = {'&': 'and', '|': 'or', '!': 'not', '(': '(', ')': ')'}
        _Token = namedtuple('Token', ['name', 'value'])
        logger.debug("_tokenize: expr {} {}".format(expr, type(expr)))
        tokens = []
        for i in expr:
            logger.debug("_tokenize: i: {}".format(i))
            if isinstance(i, Match):
                tokens.append(_Token(token_map.get(i, 'EXPR'), i))
            elif isinstance(i, ChildMatch):
                tokens.append(_Token(token_map.get(i, 'CHILD'), i))
            elif isinstance(i, Count):
                tokens.append(_Token(token_map.get(i, 'COUNT'), i))
            elif isinstance(i, GenericFunction):
                tokens.append(_Token(token_map.get(i, 'GENERIC'), i))
            elif isinstance(i, CompareOS):
                tokens.append(_Token(token_map.get(i, 'CMPOS'), i))
            elif isinstance(i, BlockMatch):
                tokens.append(_Token(token_map.get(i, 'BLOCK'), i))
            elif isinstance(i, CmdParse):
                tokens.append(_Token(token_map.get(i, 'CMDP'), i))
            elif isinstance(i, CmdFsmParse):
                tokens.append(_Token(token_map.get(i, 'CMDPFSM'), i))
            elif isinstance(i, NapalmGet):
                tokens.append(_Token(token_map.get(i, 'NAPGET'), i))
            elif isinstance(i, ParentChildMatch):
                tokens.append(_Token(token_map.get(i, 'PCMATCH'), i))
            elif i in ''.join(token_map):
                tokens.append(_Token(token_map.get(i), i))
            else:
                logger.critical("Error Tokenizing: {}".format(expr))
                raise ValueError("token {} is not recognized".format(i))
        logger.debug("_tokenize: tokens: {}".format(tokens))
        return tokens

    def _match(self, parse, cli_commands=None, hard_dict=None, get_methods_output=None):
        line = ''
        try:
            for token in self.tokens:
                if token.name == 'EXPR':
                    result = self._parse(token, parse)
                elif token.name == 'CHILD':
                    result = self._parse(token, parse)
                elif token.name == 'COUNT':
                    result = self._parse(token, parse)
                elif token.name == 'BLOCK':
                    result = self._parse(token, parse)
                elif token.name == 'GENERIC':
                    result = self._generic(token, parse, cli_commands=cli_commands)
                elif token.name == 'CMPOS':
                    result = self._compare_os(token, hard_dict=hard_dict)
                elif token.name == 'CMDP':
                    result = self._cmd_parse(token, cli_commands=cli_commands)
                elif token.name == 'CMDPFSM':
                    result = self._cmd_parse(token, cli_commands=cli_commands)
                elif token.name == 'NAPGET':
                    result = self._napalm_get(token, get_methods_output=get_methods_output)
                elif token.name == 'PCMATCH':
                    result = self._parse(token, parse)
                else:
                    result = token.name
                line = '{} {}'.format(line, result)
            logger.debug("_match: line {}".format(line))
            return eval(line)
        except CannotCompleteAnalysisError as err:
            logger.critical(err)
            raise

    def confirm_match(self, parse, cli_commands=None, hard_dict=None, get_methods_output=None, modify_config=False):
        """
        Takes the config of the device, splits it into lines, creates a CiscoConfParse object
        and determines if the configuration matches the rule.

        The list of tokens are parsed

        Examples:
        logging_server_rule = Rule("Logging to a syslog server not enabled ")
        logging_server_rule.set_confirm_match(logging_server_match)
        In this case, the Rule looks in the config for "^logging\s+server"
        The Rule is matched if the configuration line is absent (the False in the child part of the Match)
        and a True is returned

        NX_OS_Redundant_NTP_Servers_not_Configured_rule = Rule('No redundant NTP server')
        NX_OS_Redundant_NTP_Servers_not_Configured_rule.set_confirm_match(NX_OS_Redundant_NTP_Servers_not_Configured_count)
        In this case, the Rule looks in the config for r"^ntp +server +\d+.\d+.\d+.\d+ +use-vrf +management"
        It counts (Count object) the number of occurrences of this configuration line
        The Rule is matched and True is returned if the occurrence of this configuration is less than two

        loopguard_no_vpc_ports_rule = Rule("Loopguard Enabled Globally with vPC and on vPC Ports")
        loopguard_no_vpc_ports_rule.set_confirm_match(feature_vpc_match, "&", "(",
                                                  "(",
                                                  global_loopguard_match,
                                                  "&",
                                                  interface_vpc_no_loopguard_match,
                                                  ")",
                                                  "|",
                                                  "(",
                                                  global_no_loopguard_match,
                                                  "&",
                                                  interface_vpc_loopguard_match,
                                                  ")", ")"
                                                  )
        In this case, the rule has five match objects to evaluate
        feature_vpc_match = Match("feature_vpc", "global", (True, r"^feature\s+vpc"))
        This match looks for feature vpc and returns True if present
        global_loopguard_match = Match("global_loopguard", "global", (True, r"^spanning-tree\s+loopguard\s+default"))
        This match looks for the global command "spanning-tree loopguard default" and returns true if present
        global_no_loopguard_match = Match("global_no_loopguard", "global", (False, r"^spanning-tree\s+loopguard\s+default"))
        This match returns True if loopguard is not enabled globally
        interface_vpc_no_loopguard_match = Match("interface_vpc_no_loopguard", r"interface port-channel", [(True, r"vpc\s+"), (False, r"no\s+spanning-tree\s+guard\s+loop")])
        This match looks for vpc interfaces not configured with "no spanning-tree guard loop"
        interface_vpc_loopguard_match = Match("interface_vpc_loopguard", r"interface port-channel", [(True, r"vpc\s+"), (True, r"spanning-tree\s+guard\s+loop")])
        This match looks for vpc interfaces configured with "spanning-tree guard loop"
        If we assume the above matches evaluate to True, False, True, False, False, respectively, the rule
        will evaluate the expression True and ((False and False) or (True and False)) and return False

        Additionally, if applicable, the results of the configuration searches are saved in the self.objects attribute
        For instance, if the above rule evaluated to True, because the results were
        True and ( ( True and True ) or ( False and False ) )
        the following dictionary might be available for later use
        {'global_loopguard': [[<IOSCfgLine # 151 'spanning-tree loopguard default'>]],
        'feature_vpc': [[<IOSCfgLine # 38 'feature vpc'>]],
        'interface_vpc_loopguard': [[]],
        'global_no_loopguard': [[<IOSCfgLine # 151 'spanning-tree loopguard default'>]],
        'interface_vpc_no_loopguard': [[<IOSCfgLine # 450 'interface port-channel1'>, <IOSCfgLine # 475 'interface port-channel11'>, <IOSCfgLine # 489 'interface port-channel12'>, <IOSCfgLine # 501 'interface port-channel91'>, <IOSCfgLine # 513 'interface port-channel92'>]]}
         Each value in the dictionary is a list of IOSCfgLine objects

        loopback_host_address_rule = Rule("Loopback Interface Not Configured With Host Address")
        loopback_host_address_rule.set_confirm_match(loopback_host_address_match)
        In this case the Match object has multiple children
        loopback_host_address_match = Match("loopback_host_address", r"interface [lL]oopback", ["ip address", (False, r"\s+ip address\s+[\d\.]+(/32|\s+255.255.255.255)")])
        We are looking for loopback interfaces that have an IP address and do not have an IP address with a 32 bit host mask
        If any loopbacks meet both of these conditions, a True is returned

        nxos_lacp_not_enabled_on_all_port_channels_match = Match("nxos_lacp_not_enabled_on_all_port_channels", r"^interface", [(True, r"^\s+channel-group\s+\d+"), (False, r"^\s+switchport\s+mode\s+fex-fabric"),
                                                                                                                           (True, r"^\s+channel-group\s+\d+$"), (True, r"^\s+channel-group\s+\d+mode\s+on")])
        nxos_port_channel_numbers_child_match = ChildMatch("nxos_port_channel_numbers", r"^interface Eth", r"^\s+channel-group\s+(\d+)")
        nxos_lacp_not_enabled_on_all_port_channels_rule = Rule("LACP Not Enabled On All Port-Channels")
        nxos_lacp_not_enabled_on_all_port_channels_rule.set_confirm_match(nxos_lacp_not_enabled_on_all_port_channels_match,
                                                                      "&",
                                                                      nxos_port_channel_numbers_child_match)
        We are looking for portchannel links without LACP not configured.
        The ChildMatch object looks for configuration objects that matches the parent regex and the child regex. Then the children
        of the parent object are searched for a match to the child regex and the tuple of the regex capture groups is returned.

        :param showrun: str, configuration of the device
        :return: Bool
        """
        self.objects = {}
        result = self._match(parse, cli_commands=cli_commands, hard_dict=hard_dict, get_methods_output=get_methods_output)
        pcfg = parse
        if modify_config and result:
            template = self.generate_config()
            parse = update_config(template, parse)
            pcfg = parse
        return result, self.objects, pcfg

    def _parse(self, token, parse):
        logger.debug("_confparsed_config: rule: {}".format(self.exception))
        result, results = token.value.run(parse)
        self.objects[token.value.name] = results
        logger.debug("_confparsed_config: self.ojects: {}".format(self.objects))
        logger.debug("_confparsed_config: final result {}".format(result))
        return result

    def _generic(self, token, parse, cli_commands=None):
        """

        :param token:
        :param parse:
        :return:
        """
        try:
            if cli_commands:
                result, self.objects[token.value.name] = token.value.func(parse, cli_commands)
            else:
                result, self.objects[token.value.name] = token.value.func(parse)
            logger.debug("_generic: result: {}, self.objects: {}".format(result, self.objects))
        except CannotCompleteAnalysisError as err:
            exc_type, exc_value, exc_traceback = sys.exc_info()
            stacktrace = traceback.extract_tb(exc_traceback)
            logger.critical("_generic: error: {}, Failed Verifying Rule: {}".format(err, self.exception))
            logger.debug(sys.exc_info())
            logger.debug(stacktrace)
            raise
        return result

    @property
    def cli_commands(self):
        return self._cli_commands

    @cli_commands.setter
    def cli_commands(self, *cmds):
        """

        example: rule.set_cli("show module", "show fex detail")


        :param cmds: list of command strings whose output is needed for the rule evaluation. The strings must match
                    the command name string in Mimir
        :return: None
        """
        logger.debug("set_cli: cmds: {}".format(cmds))
        self.need_cli = True
        self._cli_commands = set(cmds)

    def append_cli_commands(self, cmds):
        logger.debug("append_cli_commands: {}".format(cmds))
        if isinstance(cmds, list) or isinstance(cmds, tuple):
            cmds = set(cmds)
        elif isinstance(cmds, str):
            cmds = set([cmds])
        logger.debug("append_cli: cmds: {}".format(cmds))
        self.need_cli = True
        self._cli_commands = self._cli_commands | cmds

    @property
    def get_list(self):
        return self._get_list

    @get_list.setter
    def get_list(self, *cmds):
        """

        example: rule.set_cli("show module", "show fex detail")


        :param cmds: list of command strings whose output is needed for the rule evaluation. The strings must match
                    the command name string in Mimir
        :return: None
        """
        logger.debug("get_list: cmds: {}".format(cmds))
        self.need_get = True
        self._get_list = set(cmds)

    def append_get_commands(self, cmds):
        logger.debug("append_get_commands: {}".format(cmds))
        if isinstance(cmds, list) or isinstance(cmds, tuple):
            cmds = set(cmds)
        elif isinstance(cmds, str):
            cmds = set([cmds])
        logger.debug("append_get: cmds: {}".format(cmds))
        self.need_get = True
        self._get_list = self._cli_commands | cmds

    def _compare_os(self, token, hard_dict=None):
        """

        :param token:
        :param hard_dict:
        :return:
        """
        if not hard_dict:
            logger.critical("_compare_os: Missing dictionary.")
            raise ValueError("MissingParameter: A dictionary containing the device OS version - similar to the output of the"
                                   "Mimir NP Hardware API - must be included. A key of 'swVersion' must be included.")
        try:
            operator = token.value.operator
            reference = token.value.reference_release
            device_os = hard_dict['swVersion']
            result = parser(operator, device_os, reference)
        except:
            exc_type, exc_value, exc_traceback = sys.exc_info()
            stacktrace = traceback.extract_tb(exc_traceback)
            logger.critical("_compare_os: error: {}, Failed Verifying OS".format(self.exception))
            logger.debug(sys.exc_info())
            logger.debug(stacktrace)
            raise
        return result

    def _cmd_parse(self, token, cli_commands=None):
        """

        :param token:
        :param cli_commands: dictionary of command outputs
        :return:
        """
        if cli_commands is None:
            logger.critical("_cmd_parse: Dictionary of cli command output expected.")
            raise ValueError("Dictionary of cli command output expected.")

        logger.debug("_cmd_parse: rule: {}, patterns: {}".format(self.exception, token.value.parselist))
        logger.debug(cli_commands)
        result, results = token.value.run(cli_commands)
        self.objects[token.value.name] = results
        logger.debug("_cmd_parse: self.ojects: {}".format(self.objects))
        logger.debug("_cmd_parse: final result {}".format(result))
        return result

    def _check_for_cli(self):
        for token in self.tokens:
            logger.debug("checking {} for command_list".format(token))
            if hasattr(token.value, "command_list"):
                logger.debug("found command list")
                self.append_cli_commands(set(token.value.command_list))
                logger.debug("new command list is {}".format(self.cli_commands))

    def _napalm_get(self, token, get_methods_output=None):
        logger.debug("_napalm_get: rule: {}, get_list: {}".format(self.exception, token.value.get_list))
        if get_methods_output is None:
            logger.critical("_napalm_get: Dictionary of get method command output expected.")
            raise ValueError("Dictionary of get method command output expected.")
        result, results = token.value.run(get_methods_output)
        self.objects[token.value.name] = results
        logger.debug("_cmd_parse: self.ojects: {}".format(self.objects))
        logger.debug("_cmd_parse: final result {}".format(result))
        return result

    def _check_for_get(self):
        for token in self.tokens:
            logger.debug("checking {} for get_list".format(token))
            if hasattr(token.value, "get_list"):
                logger.debug("found get list")
                self.append_get_commands(set(token.value.get_list))
                logger.debug("new get list is {}".format(self.get_list))