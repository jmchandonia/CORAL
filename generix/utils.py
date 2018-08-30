import re

__TERM_PATTERN = re.compile('(.+)<(.+)>')


def check_term_format(value):
    m = __TERM_PATTERN.findall(value)
    return m is not None
