from __future__ import print_function
from __future__ import unicode_literals


# stdlib
import re


# ==============================================================================


RE_newlines_1p__full = re.compile('^\n+$')
RE_newlines_2p__full = re.compile('^\n\n+$')
RE_newlines_3p = re.compile('\n\n\n+')
RE_space_tab_only = re.compile('^[\ \t]+$')
RE_space_tab_p = re.compile('[\ \t]+')
RE_whitespace_meh = re.compile('\n[\ \t]+(?![\d\*])')


# ==============================================================================


# escaping attributes
def safe_title(title):
    if title and '"' in title:
        title = title.replace('"', '\\"')
    return title


def is_token_newlines_1p(token):
    if token['type'] == 'SpaceCharacters':
        if RE_newlines_1p__full.match(token['data']):
            return True
    return False


def is_token_newlines_2p(token):
    if token['type'] == 'SpaceCharacters':
        if RE_newlines_2p__full.match(token['data']):
            return True
    return False


def is_list_upcoming(tokens):
    # ???: maybe iterate the raw tokens/idx and keep looking across multiple spaces?
    # tokens: token_next, token_next1
    if tokens[0]:
        if tokens[0].get('name') in ('ul', 'ol'):
            return True
        if tokens[0]['type'] == 'SpaceCharacters':
            if tokens[1]:
                if tokens[1].get('name') in ('ul', 'ol'):
                    return True
    return False


def clean_token_attributes(token, name=None, allowed_attributes=None):
    if name is None:
        name = token.get('name')
    if 'data' in token:
        if name in allowed_attributes:
            for _key in list(token["data"].keys()):
                # _key = (namespace, name)
                if _key[1] not in allowed_attributes[name]:
                    del token["data"][_key]
        else:
            token["data"] = {}
    return token


# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
