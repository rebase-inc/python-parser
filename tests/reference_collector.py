import os
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
from flask import current_user
from a.b import c as d
from yfget import YahooFinanceGet, Converter
from multiprocessing import current_process as process
from os.path import abspath, dirname
from os.path import abspath as apath
from pprint import (
    PrettyPrinter,
)
import spiral.tools
from spiral.messages import HELPSTRING, COMMAND_CATEGORIES
from spiral.tools import ProgressWrapper

CATEGORIES = spiral.tools.enum(*COMMAND_CATEGORIES.keys())

from ...package.cousins.cooper import joe as cooter
from ..cousins.hogg import Jefferson as Boss
import my_private_pkg

class Foo(object):
    def __init__(self, thing):
        self.thing = thing

f = Foo(['asdf','asdf'])
f.thing[0]

d()

some_counter = kollections.Counter()

root_logger = logging.getLogger()

test_var = 'something'
test_var

PrettyPrinter()

somebody = current_user()

log = getLogger(__name__)
value = Converter.str_to_nplaces('5', n=3)

abspath('.')
dirname('foo/bar/baz.py')

process().name = 'Foo'

print([os.path.abspath(foo) for foo in [1,2,3,4]])

Boss().hates(apath(cooter.path))

file_obj = ProgressWrapper(open(src, 'rb'))


my_private_pkg.is_da_bomb()


'''


class Collector(TestCase):

    def setUp(self):
        self.py3_ast = parse(py3_code)

    def test_run(self):
        self.assertTrue(self.py3_ast)
        private_modules = ['my_private_pkg', 'yfget', 'spiral']
        reference_collector = ReferenceCollector(private_modules)
        reference_collector.visit(self.py3_ast)
        uses = reference_collector.use_count
        self.assertEqual(uses.pop('flask.current_user'), 1)
        self.assertEqual(uses.pop('a.b.c'), 1)
        self.assertEqual(uses.pop('__stdlib__.collections.Counter'), 1)
        self.assertEqual(uses.pop('__stdlib__.logging.getLogger'), 2)
        self.assertEqual(uses.pop('__stdlib__.multiprocessing.current_process.name'), 1)
        self.assertEqual(uses.pop('__stdlib__.os.path.abspath'), 3)
        self.assertEqual(uses.pop('__stdlib__.os.path.dirname'), 1)
        self.assertEqual(uses.pop('__stdlib__.pprint.PrettyPrinter'), 1)
        self.assertEqual(uses.pop('__stdlib__.__grammar__.comprehension'), 1)
        self.assertEqual(uses.pop('__stdlib__.__grammar__.Load'), 4)
        self.assertEqual(uses.pop('__stdlib__.__grammar__.Assign'), 11)
        self.assertEqual(uses.pop('__stdlib__.__grammar__.Attribute'), 24)
        self.assertEqual(uses.pop('__stdlib__.__grammar__.Call'), 21)
        self.assertEqual(uses.pop('__stdlib__.__grammar__.Expr'), 9)
        self.assertEqual(uses.pop('__stdlib__.__grammar__.Import'), 3)
        self.assertEqual(uses.pop('__stdlib__.__grammar__.ImportFrom'), 13)
        self.assertEqual(uses.pop('__stdlib__.__grammar__.Module'), 1)
        self.assertEqual(uses.pop('__stdlib__.__grammar__.Name'), 27)
        self.assertEqual(uses.pop('__stdlib__.__grammar__.Str'), 8)
        self.assertEqual(uses.pop('__stdlib__.__grammar__.List'), 2)
        self.assertEqual(uses.pop('__stdlib__.__grammar__.ListComp'), 1)
        self.assertEqual(uses.pop('__stdlib__.__grammar__.Num'), 6)
        self.assertEqual(uses.pop('__stdlib__.__grammar__.ClassDef'), 1)
        self.assertEqual(uses.pop('__stdlib__.__grammar__.FunctionDef'), 1)
        self.assertEqual(uses.pop('__stdlib__.__grammar__.Index'), 1)
        self.assertEqual(uses.pop('__stdlib__.__grammar__.Subscript'), 1)
        self.assertEqual(uses.pop('__stdlib__.__grammar__.arg'), 2)
        self.assertEqual(uses.pop('__stdlib__.__grammar__.arguments'), 1)
        self.assertEqual(uses.pop('__stdlib__.__grammar__.keyword'), 1)
        self.assertEqual(uses.pop('__stdlib__.__grammar__.Starred'), 1)
        self.assertEqual(uses.pop('__private__.my_private_pkg.is_da_bomb'), 1)
        self.assertEqual(uses.pop('__private__.yfget.Converter.str_to_nplaces'), 1)
        self.assertEqual(uses.pop('__private__.spiral.tools.enum'), 1)
        self.assertEqual(uses.pop('__private__.spiral.messages.COMMAND_CATEGORIES.keys'), 1)
        self.assertEqual(uses.pop('__private__.spiral.tools.ProgressWrapper'), 1)
        self.assertEqual(dict(uses), {})

    # def test_private_module(self):
    #     private_modules = ['spiral']
    #     reference_collector = ReferenceCollector(private_modules)
    #     with open(os.path.dirname(__file__) + '/testfile', 'r') as f:
    #         reference_collector.visit(parse(f.read()))
    #     print(list(filter(lambda thing: thing.startswith('spiral'), reference_collector.use_count)))

