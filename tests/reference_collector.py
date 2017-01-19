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
from multiprocessing import current_process as process
from os.path import abspath, dirname
from os.path import abspath as apath
from pprint import (
    PrettyPrinter,
)

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

abspath('.')
dirname('foo/bar/baz.py')

process().name = 'Foo'

print([os.path.abspath(foo) for foo in [1,2,3,4]])

Boss().hates(apath(cooter.path))


my_private_pkg.is_da_bomb()


'''


class Collector(TestCase):

    def setUp(self):
        self.py3_ast = parse(py3_code)

    def test_run(self):
        self.assertTrue(self.py3_ast)
        private_modules = ['my_private_pkg']
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
        self.assertEqual(uses.pop('__stdlib__.comprehension'), 1)
        self.assertEqual(uses.pop('__stdlib__.Load'), 3)
        self.assertEqual(uses.pop('__stdlib__.Assign'), 8)
        self.assertEqual(uses.pop('__stdlib__.Attribute'), 18)
        self.assertEqual(uses.pop('__stdlib__.Call'), 16)
        self.assertEqual(uses.pop('__stdlib__.Expr'), 9)
        self.assertEqual(uses.pop('__stdlib__.Import'), 2)
        self.assertEqual(uses.pop('__stdlib__.ImportFrom'), 10)
        self.assertEqual(uses.pop('__stdlib__.Module'), 1)
        self.assertEqual(uses.pop('__stdlib__.Name'), 21)
        self.assertEqual(uses.pop('__stdlib__.Str'), 6)
        self.assertEqual(uses.pop('__stdlib__.List'), 2)
        self.assertEqual(uses.pop('__stdlib__.ListComp'), 1)
        self.assertEqual(uses.pop('__stdlib__.Num'), 5)
        self.assertEqual(uses.pop('__stdlib__.ClassDef'), 1)
        self.assertEqual(uses.pop('__stdlib__.FunctionDef'), 1)
        self.assertEqual(uses.pop('__stdlib__.Index'), 1)
        self.assertEqual(uses.pop('__stdlib__.Subscript'), 1)
        self.assertEqual(uses.pop('__stdlib__.arg'), 2)
        self.assertEqual(uses.pop('__stdlib__.arguments'), 1)
        self.assertEqual(uses.pop('__private__.my_private_pkg.is_da_bomb'), 1)
        self.assertEqual(dict(uses), {})


