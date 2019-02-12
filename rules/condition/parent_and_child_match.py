import logging
import re

from rules.condition.abs_cond import AbsCondition

logger = logging.getLogger(__name__)


class ParentChildMatch(AbsCondition):
    def __init__(self, name, parent_regex, child_filter_regexes=None, child_match_regexes=None):
        """

        Examples:
        interface_vpc_no_loopguard_match = Match("interface_vpc_no_loopguard", r"interface port-channel", [(True, r"vpc\s+"), (False, r"no\s+spanning-tree\s+guard\s+loop")])
        self.parent_regex = interface port-channel
        self.child_regexes = [(True, 'vpc\\s+'), (True, 'spanning-tree\\s+guard\\s+loop')]

        interface_vpc_loopguard_match = Match("interface_vpc_loopguard", r"interface port-channel", [(True, r"vpc\s+"), (True, r"spanning-tree\s+guard\s+loop")])

        loopback_host_address_match = Match("loopback_host_address",
                                      r"interface [lL]oopback",
                                      ["ip address", (False, r"\s+ip address\s+[\d\.]+(/32|\s+255.255.255.255)")])
        In this case, the child has two regexes, the first, "ip address" will be automatically converted to
        (True, "ip address")
        self.parent_regex = interface [lL]oopback
        self.child_regexes = [(True, 'ip address'), (False, '\\s+ip address\\s+[\\d\\.]+(/32|\\s+255.255.255.255)')]

        :type parent_regex: string, regex string
        :type child_filter_regexes: list of tuples, if there are multiple children in a Match object an "and" operaation is
        performed, the parent objects are first pulled and then checked for the presence of each child in turn.
        :type child_match_regexes: list or tuple of regexes
        If the parent does not have a child, it is discarded.
        If any parent objects are left after running them against all children, a True is returned.

        Returns result and answer
        result is True or False

        Example answer:
        {'parents': [[<IOSCfgLine # 1621 'interface Port-channel1.2'>, <IOSCfgLine # 1638 'interface Port-channel1.10'>,
        <IOSCfgLine # 1662 'interface Port-channel1.12'>, <IOSCfgLine # 1685 'interface Port-channel1.13'>,
        <IOSCfgLine # 1707 'interface Port-channel1.14'>, <IOSCfgLine # 1728 'interface Port-channel1.15'>,
        <IOSCfgLine # 1751 'interface Port-channel1.30'>, <IOSCfgLine # 1774 'interface Port-channel1.44'>,
        <IOSCfgLine # 1798 'interface Port-channel1.77'>, <IOSCfgLine # 1807 'interface Port-channel1.90'>,
        <IOSCfgLine # 1818 'interface Port-channel1.555'>, <IOSCfgLine # 1835 'interface Port-channel1.802'>]],
        'children': {'interface Port-channel1.2': [[('10.1.1.1', '255.255.252.0')], [('10.3.3.3',)]],
        'interface Port-channel1.10': [[('10.4.4.4', '255.255.255.128')], [('10.5.5.5',)]],
        'interface Port-channel1.12': [[('10.6.6.6', '255.255.255.128')], [('10.7.7.7',)]],
        'interface Port-channel1.13': [[('10.8.8.8', '255.255.255.192')], [('10.9.9.9',)]],
        'interface Port-channel1.14': [[('10.10.10.10', '255.255.255.192')], [('10.11.11.11',)]]}}

        """

        super().__init__(name)
        logger.debug("Parent_and_Child_Match: __init__: parent: {}, child filters {}, child matches {}".format(parent_regex, child_filter_regexes, child_match_regexes))
        self.parent_regex = parent_regex
        logger.debug("Match: __init__: {}".format(self.parent_regex))
        self.child_regexes = []
        if child_filter_regexes:
            if isinstance(child_filter_regexes, str):
                self.child_regexes = [(True, child_filter_regexes)]
            elif isinstance(child_filter_regexes, tuple) and len(child_filter_regexes) == 2:
                self.child_regexes = [child_filter_regexes]
            elif isinstance(child_filter_regexes, list):
                for regex in child_filter_regexes:
                    if (isinstance(regex, tuple) or isinstance(regex, list)) and len(regex) == 2:
                        self.child_regexes.append(regex)
                    elif isinstance(regex, str):
                        self.child_regexes.append((True, regex))
                    else:
                        logger.debug("Parent_and_Child_Match: __init__: no match on child filter regex {}".format(regex))
        logger.debug("Parent_and_Child_Match: __init__: self.child_filter_regexes {}".format(self.child_regexes))

        self.child_match_regexes = child_match_regexes
        if isinstance(child_match_regexes, str):
            self.child_match_regexes = [child_match_regexes]
        logger.debug("Parent_and_Child_Match: __init__: self.child_match_regexes {}".format(self.child_match_regexes))

    def __str__(self):
        line = "parent: {}, child filter regexes {}, child match regexes".format(self.parent_regex, self.child_regexes, self.child_match_regexes)
        return line

    def run(self, parse):
        results = []
        parent = self.parent_regex
        children = self.child_regexes
        logger.debug("_confparsed_config: match: {}, parent {}, children {}".format(self.name, parent, children))
        result = True
        # if there are multiple children in a Match object, the parent object is pulled and then checked for each child, if there are
        # any parent objects left after running them against all children, a True is returned
        if 'global' in parent.lower():
            for b, c in children:
                logger.debug("_confparsed_config: global child b {}, c {}".format(b, c))
                answer = parse.find_objects(c)
                results.append(answer)
                answer = bool(answer)
                logger.debug("_confparsed_config: global child answer: {}".format(answer))
                if not b:
                    answer = not answer
                logger.debug("_confparsed_config: global: answer {}".format(answer))
                result = result and answer
                logger.debug("_confparsed_config: global: result: {}".format(result))
        else:
            objs = parse.find_objects(parent)
            for b, c in children:
                logger.debug("_confparsed_config: child b {}, c {}".format(b, c))
                if b:
                    objs = [obj for obj in objs if obj.re_search_children(c)]
                else:
                    objs = [obj for obj in objs if not obj.re_search_children(c)]
                logger.debug("_confparsed_config: new objs {}".format(objs))
            logger.debug("_confparsed_config: parent: {}, objs {}".format(parent, objs))
            results.append(objs)
            result = bool(objs)
            logger.debug("_confparsed_config: result: {}".format(result))
        logger.debug("_confparsed_config: results: {}".format(results))
        logger.debug("_confparsed_config: final result {}".format(result))

        answers = {'parents': results, 'children': {}}
        if self.child_match_regexes:
            for objects in results:
                logger.debug("objects: {}".format(objects))
                for object in objects:
                    logger.debug("object: {}".format(object))
                    answers['children'][object.text] = []
                    for child in self.child_match_regexes:
                        logger.debug("_parent_child_parse: object.text: {}".format(object.text))
                        logger.debug("child match regex: {}".format(child))
                        lineobj = object.re_search_children(child)
                        logger.debug("_parent_child_parse: lineobj: {}".format(lineobj))
                        if lineobj:
                            logger.debug("_parent_child_parse: lineobj[0].text: {}".format(lineobj[0].text))
                            children = [re.search(child, obj.text) for obj in lineobj]
                            children_groups = []
                            if children:
                                children_groups = [child.groups() for child in children]
                            if not children_groups and children:
                                children_groups = [child.group() for child in children]
                            result = result and bool(children_groups)
                            logger.debug("_parent_child_parse: children: {}".format(children_groups))
                            answers['children'][object.text].append(children_groups)

        logger.debug("_parent_child_parse: answers: {}".format(answers))
        logger.debug("_parent_child_parse: final result {}".format(result))
        return str(result), answers
