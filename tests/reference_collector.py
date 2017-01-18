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
            '__grammar__.Assign': 3,
            '__grammar__.Attribute': 5,
            '__grammar__.Call': 8,
            '__grammar__.Expr': 3,
            '__grammar__.Import': 2,
            '__grammar__.ImportFrom': 8,
            '__grammar__.Load': 4,
            '__grammar__.Module': 1,
            '__grammar__.Name': 11,
            '__grammar__.Store': 1,
            '__grammar__.Str': 2,
            '__stdlib__.collections': 1,
            '__stdlib__.copy': 1,
            '__stdlib__.logging': 4,
            '__stdlib__.multiprocessing': 2,
            'my_private_pkg': 2,
            '__stdlib__.os.path': 4,
            '__stdlib__.pprint': 1,
            '__stdlib__.re': 1,
        }
        #pprint(expectedUses)
        self.assertEqual(dict(uses), expectedUses)


