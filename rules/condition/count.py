import logging

logger = logging.getLogger('count')


class Count:
    def __init__(self, name, parent_regex, child_regex):
        """
        Examples:
        NX_OS_Redundant_NTP_Servers_not_Configured_count = Count("NX_OS_Redundant_NTP_Servers_not_Configured", "global", (True, r"^ntp +server +\d+.\d+.\d+.\d+ +use-vrf +management", "< 2"))
        self.parent_regex = global
        self.child_regexes = (True, '^ntp +server +\\d+.\\d+.\\d+.\\d+ +use-vrf +management', '< 2')
        Only one child regex is allowed
        If the parent is global, only True is allowed in the child

        :param parent_regex: a string
        :param child_regexes: a single list or tuple of the form (t/f, regex, comparator string).
        """
        super().__init__(name)
        logger.debug("Count: __init__: parent: {}, child {}".format(parent_regex, child_regex))
        self.parent_regex = parent_regex
        if isinstance(child_regex, tuple) or isinstance(child_regex, list):
            if len(child_regex) == 2:
                self.child_regex = ((True, child_regex[0], child_regex[1]))
            elif len(child_regex) == 3:
                self.child_regex = child_regex
            else:
                logger.debug("Count: __init__: no match on child regex {}".format(child_regex))
        logger.debug("Count: __init__: self.child_regexes {}".format(self.child_regex))

    def __str__(self):
        line = "parent: {}, child {}".format(self.parent_regex, self.child_regex)
        return line

    def run(self, parse):
        """

        :param token:
        :return:
        """
        results = []
        parent = self.parent_regex
        child = self.child_regex
        logger.debug("count: name {} parent {}, child {}".format(self.name, parent, child))
        if 'global' in parent.lower():
            b, c, d = child
            logger.debug("count: global child b {}, c {}, d {}".format(b, c, d))
            if b:
                answer = parse.find_objects(c)
                results.append(answer)
                answer = len(answer)
                logger.debug("_count: global child answer: {}".format(answer))
            if not b:
                raise SyntaxError("Unsupported Count Opotion: False is unsupported if parent is global")
            result = eval('{} {}'.format(answer, d))
            logger.debug("_count: global: answer {}".format(result))
        else:
            objs = parse.find_objects(parent)
            b, c, d = child
            logger.debug("_count: child b {}, c {}, d {}".format(b, c, d))
            if b:
                objs = [obj for obj in objs if obj.re_search_children(c)]
            else:
                objs = [obj for obj in objs if not obj.re_search_children(c)]
            logger.debug("_count: new objs {}".format(objs))
            logger.debug("_count: parent: {}, objs {}".format(parent, objs))
            results.append(objs)
            answer = len(objs)
            result = eval('{} {}'.format(answer, d))
            logger.debug("_count: result: {}".format(result))
        logger.debug("_count: final result {}".format(result))
        return str(result), results
