import logging

from rules.condition.abs_cond import AbsCondition

logger = logging.getLogger(__name__)


class Match(AbsCondition):
    def __init__(self, name, parent_regex, child_regexes):
        """

        Examples:
        Match("logging_server", "global", (False, "^logging\s+server"))
        self.parent_regex = global
        self.child_regexes = [(False, '^logging\\s+server')]

        default_vdc_match = Match("default_vdc", "global", "^vdc.*?id 1")
        copp_profile_match = Match("copp_profile", "global", (False, r"^copp\s+profile\s+(strict|dense)"))

        feature_vpc_match = Match("feature_vpc", "global", (True, r"^feature\s+vpc"))
        global_loopguard_match = Match("global_loopguard", "global", (True, r"^spanning-tree\s+loopguard\s+default"))
        global_no_loopguard_match = Match("global_no_loopguard", "global", (False, r"^spanning-tree\s+loopguard\s+default"))

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
        child_regexes: list of tuples, if there are multiple children in a Match object an "and" operaation is
        performed, the parent objects are first pulled and then checked for the presence of each child in turn.
        If the parent does not have a child, it is discarded.
        If any parent objects are left after running them against all children, a True is returned.
        """

        super().__init__(name)
        logger.debug("Match: __init__: parent: {}, child {}".format(parent_regex, child_regexes))
        self.parent_regex = parent_regex
        logger.debug("Match: __init__: {}".format(self.parent_regex))
        self.child_regexes = []
        if isinstance(child_regexes, str):
            self.child_regexes = [(True, child_regexes)]
        elif isinstance(child_regexes, tuple) and len(child_regexes) == 2:
            self.child_regexes = [child_regexes]
        elif isinstance(child_regexes, list):
            for regex in child_regexes:
                if (isinstance(regex, tuple) or isinstance(regex, list)) and len(regex) == 2:
                    self.child_regexes.append(regex)
                elif isinstance(regex, str):
                    self.child_regexes.append((True, regex))
                else:
                    logger.debug("Match: __init__: no match on child regex {}".format(regex))
        logger.debug("Match: __init__: self.child_regexes {}".format(self.child_regexes))

    def __str__(self):
        line = "parent: {}, child {}".format(self.parent_regex, self.child_regexes)
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
        return str(result), results
