import logging

from rules.condition.abs_cond import AbsCondition

logger = logging.getLogger('blockmatch')


class BlockMatch(AbsCondition):
    def __init__(self, name, block_regex):
        """

        :param name:
        :param block_regex:

        Example:
        BlockMatch("\s+route-map")
        In this instance, results is a list of strings
        ['router bgp 65534', '  neighbor 1.1.1.1 remote-as 65534', '    address-family ipv4 unicast', '
        route-map EXAMPLE out', '  neighbor 2.2.2.2 remote-as 65534', '    address-family ipv4 unicast', '
        route-map EXAMPLE out', '  neighbor 3.3.3.3 remote-as 65534', '    address-family ipv4 unicast', '
        route-map EXAMPLE out']

        """

        super().__init__(name)
        logger.debug("BlockMatch: __init__: name: {}, block {}".format(name, block_regex))
        self.block_regex = block_regex
        logger.debug("BlockMatch: __init__: {}".format(self.block_regex))

    def __str__(self):
        line = "name: {}, block_regex {}".format(self.name, self.block_regex)
        return line

    def run(self, parse):
        logger.debug("_confparsed_config: blockmatch: {}, block {}".format(self.name, self.block_regex))
        results = parse.find_blocks(self.block_regex)
        logger.debug("blockmatch: results: {}".format(results))
        result = bool(results)
        logger.debug("blockmatch: result: {}".format(result))
        return str(result), results
