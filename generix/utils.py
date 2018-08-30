import re
from .ontology import Term

__TERM_PATTERN = re.compile('(.+)<(.+)>')


def check_term_format(value):
    m = __TERM_PATTERN.findall(value)
    return m is not None


def parse_term(value):
    m = __TERM_PATTERN.findall(value)
    if m:
        term = Term(m[0][1].strip(), term_name=m[0][0].strip())
    return term
