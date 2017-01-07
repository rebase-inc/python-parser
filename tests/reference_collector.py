from ast import parse
from logging import getLogger
from pprint import pprint
from unittest import TestCase

from server import ReferenceCollector
from . import log_to_stdout


log_to_stdout()


log = getLogger(__name__)


py3_code = '''

import logging, re, collections as kollections
from copy import *
from logging import getLogger
from multiprocessing import current_process as process
from os.path import abspath
from os.path import abspath as apath
from pprint import (
    PrettyPrinter,
)

from ..cousins.cooper import joe as cooter
from ..cousins.hogg import Jefferson as Boss
import my_private_pkg


root_logger = logging.getLogger()


log = getLogger(__name__)


abspath('.')


process().name = 'Foo'


Boss().hates(apath(cooter.path))


my_private_pkg.is_da_bomb()


'''


class Collector(TestCase):

    def setUp(self):
        self.py3_ast = parse(py3_code)

    def test_run(self):
        self.assertTrue(self.py3_ast)
        uses = ReferenceCollector().visit(self.py3_ast)
        self.assertTrue(uses)
        pprint(dict(uses))
        expectedUses = {
            '__grammar__Assign': 3,
            '__grammar__Attribute': 5,
            '__grammar__Call': 8,
            '__grammar__Expr': 3,
            '__grammar__Import': 2,
            '__grammar__ImportFrom': 8,
            '__grammar__Load': 4,
            '__grammar__Module': 1,
            '__grammar__Name': 11,
            '__grammar__Store': 1,
            '__grammar__Str': 2,
            'collections': 1,
            'copy': 1,
            'logging': 4,
            'multiprocessing': 2,
            'my_private_pkg': 2,
            'os.path': 4,
            'pprint': 1,
            're': 1,
        }
        #pprint(expectedUses)
        self.assertEqual(dict(uses), expectedUses)


