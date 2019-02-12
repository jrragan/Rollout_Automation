import logging
import re

from rules.condition.abs_cond import AbsCondition

logger = logging.getLogger('childmatch')


class ChildMatch(AbsCondition):
    def __init__(self, name, parent_regex, child_regex):
        """
        Provide a parent regex string such as "interface" that identifies a configuration block
        The child regex is a regex string matching a child line within the block returned by the parent. The
        child regex includes a capture group

        Examples:
        ChildMatch("portchannel_lacp_childmatch", r"^interface", r"channel-group +(\d+)")

        :type parent_regex: regex string, "global" is not allowed
        child_regex: regex string with a capture group

        """

        super().__init__(name)
        logger.debug("ChildMatch: __init__: parent: {}, child {}".format(parent_regex, child_regex))
        self.parent_regex = parent_regex
        logger.debug("ChildMatch: __init__: {}".format(self.parent_regex))
        self.child_regex = child_regex
        logger.debug("ChildMatch: __init__: self.child_regex {}".format(self.child_regex))

    def __str__(self):
        line = "parent: {}, child {}".format(self.parent_regex, self.child_regex)
        return line

    def run(self, parse):
        parent = self.parent_regex
        child = self.child_regex
        objs = parse.find_objects_w_child(parent, child)
        answers = {'parents': objs, 'children': {}}
        logger.debug("_child_parse: name {} child parent {}, child {}".format(self.name, parent, child))
        logger.debug("_child_parse: new objs {}".format(objs))
        logger.debug("_child_parse: parent: {}, objs {}".format(parent, objs))
        for object in objs:
            logger.debug("_child_parse: object.text: {}".format(object.text))
            lineobj = object.re_search_children(child)
            logger.debug("_child_parse: lineobj: {}, lineobj[0].text".format(lineobj, lineobj[0].text))
            children = re.search(child, lineobj[0].text)
            logger.debug("_child_parse: children: {}".format(children.groups()))
            if children.groups():
                answers['children'][object.text] = children.groups()

        result = bool(answers['children'])

        logger.debug("_child_parse: answers: {}".format(answers))
        logger.debug("_child_parse: final result {}".format(result))
        return str(result), answers
