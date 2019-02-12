import logging

logger = logging.getLogger('comapareos')

class CompareOS:
    def __init__(self, operator, cmp_string):
        """
        The goal is to provide a comparison with running software on a device to some reference

        The app only compares the first n characters of the system OS where n is the length of the cmp_string
        If you provided 5.2 as the cmp_string, then only the first three characters of the system OS, which might be
        5.2(1)N1(4), would be compared. So the more specific the cmp_string, the better.

        The device or system OS is the left side of the expression. The provided cmp_string or reference OS is
        the right side.

        Examples:
        If all software releases older than 5.2 would fail a best practice check, you would define
        sw_test = CompareOS('<', '5.2')
        This is the same as device_os < 5.2

        If you only need to flag a particular release
        sw_test = CompareOS('==', '7.0(8)N1(1)')
        equivalent to device_os == 7.0(8)N1(1)

        If you need to flag a release newer than a certain rev
        sw_test = CompareOS('>', '5.2')
        Note that in this case, if you meant all releases newer than 5.2(1)N1(1), this comparison would fail with
        any release belonging to the 5.2 train, such as 5.2(1)N1(4) because only the 5.2 portion of the two strings
        would be compared. If you want 5.2(1)N1(4) to pass the comparison, you should define the comparison with
        5.2(1)N1(1) instead of 5.2.

        If all software releases
        :param operator: a string of a comparison operator, allowed values are <, <=, >, >=, ==, !=
        :param cmp_string: a string with a software version, this is the right side of the expression
        """
        self.operator = operator
        self.reference_release = cmp_string

    def __str__(self):
        line = "operator: {}, reference {}".format(self.operator, self.reference_release)
        return line