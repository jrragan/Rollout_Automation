import logging
from io import StringIO
from pprint import pprint
from time import strftime, gmtime

from rules.condition.command_fsm_parser import CmdFsmParse
from rules.condition.command_parser import CmdParse
from rules.condition.count import Count
from rules.condition.match import Match
from rules.condition.napalm_get import NapalmGet
from rules.rule import Rule
from rules.template_rule import TemplateRule
from tasks.template_task import TemplateTask
from tasks.tester_task import TestTask

LOGFILE = "rollout_test" + strftime("_%y%m%d%H%M%S", gmtime()) + ".log"
SCREENLOGLEVEL = logging.DEBUG
FILELOGLEVEL = logging.DEBUG
logformat = logging.Formatter(
    '%(asctime)s: %(process)d - %(threadName)s - %(funcName)s - %(name)s - %(levelname)s - message: %(message)s')
#
# # logging.basicConfig(level=FILELOGLEVEL,
# #                     format='%(asctime)s: %(threadName)s - %(funcName)s - %(name)s - %(levelname)s - %(message)s',
# #                     filename=LOGFILE)
# logger = logging.getLogger('rollout')
# logger.setLevel(logging.DEBUG)
#
# # screen handler
# ch = logging.StreamHandler()
# ch.setLevel(SCREENLOGLEVEL)
# ch.setFormatter(logformat)
#
# # file handle
# fh = logging.FileHandler(LOGFILE)
# fh.setLevel(FILELOGLEVEL)
# fh.setFormatter(logformat)
#
# logger.addHandler(fh)
# logger.addHandler(ch)

# create logger
logging.basicConfig(format='%(asctime)s: %(threadName)s - %(funcName)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.DEBUG)
logger = logging.getLogger('RollOut')
# logger.setLevel(logging.DEBUG)
#
# # create console handler and set level to debug
# ch = logging.StreamHandler()
# ch.setLevel(logging.DEBUG)
#
# # create formatter
# formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
#
# # add formatter to ch
# ch.setFormatter(formatter)
#
# # add ch to logger
# logger.addHandler(ch)

DEVICES = ['172.16.1.87', '172.16.1.88']


def test1():
    logger.info("Started")
    logger.info("***** Test1 - One Router Get Facts *****")
    args = {'verbose': True}
    task = TestTask(['172.16.1.76'], 'ios', 'cisco', 'cisco', optional_args=args)
    task.get_device_info()
    pprint(task.device_facts)
    pprint(task.running_config)


def test2():
    logger.info("***** Test2 - Two Router Get Facts *****")
    args = {'verbose': True}
    task = TestTask(DEVICES, 'ios', 'cisco', 'cisco', optional_args=args)
    task.get_device_info()
    pprint(task.device_facts)
    pprint(task.running_config)


def test3():
    logger.info("***** Test3 - Two Router Single Rule *****")
    args = {'verbose': True}
    tacacs_server_global_count = Count("tacacs_server_global", r"^aaa group server tacacs\+",
                                       (True, r"server\s+", ">1"))
    tacacs_server_rule = Rule("Redundant Tacacs servers not configured")
    tacacs_server_rule.set_confirm_match(tacacs_server_global_count)
    test_rules = {1: tacacs_server_rule}
    logger.debug(test_rules)
    task = TestTask(DEVICES, 'ios', 'cisco', 'cisco', rules=list(test_rules.keys()),
                    rule_objs=test_rules, optional_args=args)
    task.run_all_rules()
    pprint(task.matches)


def test4():
    logger.info("***** Tes4 - Two Router Two Rules *****")
    args = {'verbose': True}
    bgp_router_match = Match("bgp_router", "global", "^router\s+bgp")
    bgp_rule = Rule("Match BGP routing")
    bgp_rule.set_confirm_match(bgp_router_match)
    ospf_router_match = Match("ospf_router", "global", "^router\s+ospf")
    ospf_lsa_match = Match("ospf_max_lsa", r"^\s*router ospf", (False, r"max-metric router-lsa"))
    ospf_rule = Rule("Match OSPF routing")
    ospf_rule.set_confirm_match(ospf_router_match, '&', ospf_lsa_match)
    test_rules = {1: bgp_rule, 2: ospf_rule}
    task = TestTask(DEVICES, 'ios', 'cisco', 'cisco', optional_args=args)
    task.set_device_rules(list(test_rules.keys()), test_rules)
    task.run_all_rules()
    pprint(task.matches)


def test5():
    logger.info("***** Test5 - Two Router Command Rules *****")
    args = {'verbose': True}
    command = {'show cdp neighbor':
        {
            'countcmpnumzl':
                [(r'csr1000v-\d\.virl\.info', r'> 1')]
        }}
    cdp_parse = CmdParse('cdp_parse', command)
    cdp_rule = Rule("CDP Parse")
    cdp_rule.set_confirm_match(cdp_parse)
    test_rules = {1: cdp_rule}
    task = TestTask(DEVICES, 'ios', 'cisco', 'cisco', rules=list(test_rules.keys()),
                    rule_objs=test_rules, optional_args=args)
    task.run_all_rules()
    pprint(task.matches)


def test6():
    logger.info("***** Test 6 - Two Router Two Rules Template Task - No Templates *****")
    args = {'verbose': True}
    bgp_router_match = Match("bgp_router", "global", "^router\s+bgp")
    bgp_rule = Rule("Match BGP routing")
    bgp_rule.set_confirm_match(bgp_router_match)
    ospf_router_match = Match("ospf_router", "global", "^router\s+ospf")
    ospf_lsa_match = Match("ospf_max_lsa", r"^\s*router ospf", (False, r"max-metric router-lsa"))
    ospf_rule = Rule("Match OSPF routing")
    ospf_rule.set_confirm_match(ospf_router_match, '&', ospf_lsa_match)
    test_rules = {1: bgp_rule, 2: ospf_rule}
    task = TemplateTask(DEVICES, 'ios', 'cisco', 'cisco', optional_args=args)
    task.set_device_rules(list(test_rules.keys()), test_rules)
    task.run_all_rules()
    pprint(task.matches)
    pprint(task.objects)


def test7():
    logger.info("***** Test 7 - Two Router Two Template Rules Template Task - No Templates *****")
    args = {'verbose': True}
    bgp_router_match = Match("bgp_router", "global", "^router\s+bgp")
    bgp_rule = TemplateRule("Match BGP routing")
    bgp_rule.set_confirm_match(bgp_router_match)
    ospf_router_match = Match("ospf_router", "global", "^router\s+ospf")
    ospf_lsa_match = Match("ospf_max_lsa", r"^\s*router ospf", (False, r"max-metric router-lsa"))
    ospf_rule = TemplateRule("Match OSPF routing")
    ospf_rule.set_confirm_match(ospf_router_match, '&', ospf_lsa_match)
    test_rules = {1: bgp_rule, 2: ospf_rule}
    task = TemplateTask(DEVICES, 'ios', 'cisco', 'cisco', optional_args=args)
    task.set_device_rules(list(test_rules.keys()), test_rules)
    task.run_all_rules()
    pprint(task.matches)
    pprint(task.objects)


def test8():
    logger.info("***** Test 8 - Two Router Two Template Rules Template Task - Simple Templates, No variables *****")
    args = {'verbose': True}
    bgp_router_match = Match("bgp_router", "global", "^router\s+bgp")
    bgp_rule = TemplateRule("Match BGP routing")
    bgp_rule.set_confirm_match(bgp_router_match)
    template = "ip tcp path-mtu-discovery\n"
    bgp_rule.set_config_template(template)
    ospf_router_match = Match("ospf_router", "global", "^router\s+ospf")
    ospf_lsa_match = Match("ospf_max_lsa", r"^\s*router ospf", (False, r"max-metric router-lsa"))
    ospf_rule = TemplateRule("Match OSPF routing")
    ospf_rule.set_confirm_match(ospf_router_match, '&', ospf_lsa_match)
    template = "snmp-server contact network_operations@nobody.com"
    ospf_rule.set_config_template(template)
    test_rules = {1: bgp_rule, 2: ospf_rule}
    task = TemplateTask(DEVICES, 'ios', 'cisco', 'cisco', optional_args=args)
    task.set_device_rules(list(test_rules.keys()), test_rules)
    task.run_all_rules()
    task.generate_all_configs()
    pprint(task.matches)
    pprint(task.objects)
    pprint(task.generated_configs)


def test9():
    logger.info("***** Test 9 - Two Router Two Template Rules Template Task - Simple Templates, With variables *****")
    args = {'verbose': True}
    bgp_router_match = Match("bgp_router", "global", "^router\s+bgp")
    bgp_rule = TemplateRule("Match BGP routing")
    bgp_rule.set_confirm_match(bgp_router_match)
    template = "{{ objects['bgp_router'][0][0].text }}\n" \
               " shutdown\n"
    bgp_rule.set_config_template(template)
    ospf_router_match = Match("ospf_router", "global", "^router\s+ospf")
    ospf_lsa_match = Match("ospf_max_lsa", r"^\s*router ospf", (False, r"max-metric router-lsa"))
    ospf_rule = TemplateRule("Match OSPF routing")
    ospf_rule.set_confirm_match(ospf_router_match, '&', ospf_lsa_match)
    template = "{% for router in objects['ospf_router'][0] %}\n{{ router.text }}\n  max-metric router-lsa\n{% endfor %}\n"
    ospf_rule.set_config_template(template)
    test_rules = {1: bgp_rule, 2: ospf_rule}
    task = TemplateTask(DEVICES, 'ios', 'cisco', 'cisco', optional_args=args)
    task.set_device_rules(list(test_rules.keys()), test_rules)
    task.run_all_rules()
    task.generate_all_configs()
    pprint(task.matches)
    pprint(task.objects)
    pprint(task.generated_configs)
    print(task.running_config)


def test10():
    logger.info("***** Test 10 - Two Router FSM Test *****")
    args = {'verbose': True}
    template = """Value slot_id (\S+)
Value pid (\S+)
Value Required serial_number (\S+)

Start
  ^\s*SlotID\s+PID\s+SN\s+UDI
  ^\s*-+
  ^\s*${slot_id}\s+${pid}\s+${serial_number}\s+.* -> Record
"""
    template = StringIO(template)
    license_match = CmdFsmParse("license_match", [("show license udi", template, '')])
    license_rule = Rule("license")
    license_rule.set_confirm_match(license_match)
    test_rules = {1: license_rule}
    task = TemplateTask(DEVICES, 'ios', 'cisco', 'cisco', rules=list(test_rules.keys()),
                        rule_objs=test_rules, optional_args=args)
    task.run_all_rules(skip_config=True, skip_facts=True)
    pprint(task.matches)
    pprint(task.objects)


def test11():
    logger.info("***** Test 11 - Two Router FSM Test with jsonpath *****")
    args = {'verbose': True}
    template = """Value slot_id (\S+)
Value pid (\S+)
Value Required serial_number (\S+)

Start
  ^\s*SlotID\s+PID\s+SN\s+UDI
  ^\s*-+
  ^\s*${slot_id}\s+${pid}\s+${serial_number}\s+.* -> Record
"""
    template = StringIO(template)
    license_match = CmdFsmParse("license_match", [("show license udi", template, '$..serial_number')])
    license_rule = Rule("license")
    license_rule.set_confirm_match(license_match)
    test_rules = {1: license_rule}
    task = TemplateTask(DEVICES, 'ios', 'cisco', 'cisco', rules=list(test_rules.keys()),
                        rule_objs=test_rules, optional_args=args)
    task.run_all_rules(skip_config=True, skip_facts=True)
    pprint(task.matches)
    pprint(task.objects)


def test12():
    logger.info("***** Test 11 - Two Router Napalm BGP *****")
    args = {'verbose': True}
    bgp_match = NapalmGet("bgp_neighbors", [("bgp_neighbors", '$..*[@.is_up is True]')])
    bgp_rule = Rule("bgp")
    bgp_rule.set_confirm_match(bgp_match)
    test_rules = {1: bgp_rule}
    task = TemplateTask(DEVICES, 'ios', 'cisco', 'cisco', rules=list(test_rules.keys()),
                        rule_objs=test_rules, optional_args=args)
    task.run_all_rules(skip_config=True, skip_facts=True)
    pprint(task.matches)
    pprint(task.objects)


test12()
