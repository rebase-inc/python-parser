from os import environ
import ast
import json
import errno
import base64
import logging

from collections import Counter
from multiprocessing import current_process

from stdlib_list import stdlib_list

import rsyslog
from asynctcp import AsyncTcpCallbackServer

current_process().name = environ['HOSTNAME'] if 'HOSTNAME' in environ else 'python-parser'
rsyslog.setup(log_level=environ['LOG_LEVEL'] if 'LOG_LEVEL' in environ else 'DEBUG')

LOGGER = logging.getLogger()

STANDARD_LIBRARY = stdlib_list('3.5')

from ast import iter_fields

class ReferenceCollector(ast.NodeVisitor):
    # see https://greentreesnakes.readthedocs.io/en/latest/nodes.html for good reference

    def __init__(self, private_namespace):
        super().__init__()
        self.bindings = dict()
        self.use_count = Counter()
        self.bindings.update({ name: '__private__.' + name for name in private_namespace })
        self.bindings.update({ name: '__stdlib__.' + name for name in STANDARD_LIBRARY })

    def add_grammar(self, node):
        self.use_count.update(['__stdlib__.__grammar__.' + node.__class__.__name__])

    def visit(self, node):
        super().visit(node)

    def generic_visit(self, node):
        self.add_grammar(node)
        super().generic_visit(node)

    def add_binding(self, bound_name, *real_attributes):
        if bound_name in self.bindings:
            return
        elif real_attributes[0] in STANDARD_LIBRARY:
            self.bindings[bound_name] = '.'.join(['__stdlib__'] + list(real_attributes))
        elif real_attributes[0] in self.bindings:
            self.bindings[bound_name] = '.'.join([self.bindings[real_attributes[0]]] + list(real_attributes[1:]))
        else:
            self.bindings[bound_name] = '.'.join(real_attributes)

    def add_use(self, *attributes):
        if attributes[0] not in self.bindings:
            # we can't know all bindings, because of imports like "from foo import *"
            # In such a case, we can't really do anything with the reference
            return
        real_name = self.bindings[attributes[0]]
        full_name = '.'.join([real_name] + list(attributes[1:]))
        self.use_count.update([ full_name ])

    def visit_Import(self, node):
        self.add_grammar(node)
        for alias in node.names:
            self.add_binding(alias.asname or alias.name, *alias.name.split('.'))

    def visit_ImportFrom(self, node):
        self.add_grammar(node)
        if node.level == 0:
            for alias in node.names:
                real_name = node.module.split('.') + [alias.name]
                self.add_binding(alias.asname or alias.name, *real_name)
        else:
            # Relative import
            # TODO: Actually add this under __private__ namespace
            pass

    def visit_Attribute(self, attribute):
        name = self.get_name(attribute)
        self.add_use(*name)
        self.add_grammar(attribute)

    def get_name(self, node):
        if isinstance(node, ast.Name):
            return [ node.id ]
        elif isinstance(node, ast.Attribute):
            return self.get_attribute_name(node)
        elif isinstance(node, ast.Call):
            return self.get_call_name(node)
        elif isinstance(node, ast.Subscript):
            return self.get_name(node.value)
        elif isinstance(node, ast.Starred):
            return self.get_name(node.value)
        else:
            return []

    def get_attribute_name(self, attribute):
        self.add_grammar(attribute)
        attributes = []
        expression = attribute
        while isinstance(expression, ast.Attribute):
            attributes.insert(0, expression.attr)
            expression = expression.value
        attributes = self.get_name(expression) + attributes
        return attributes

    def get_call_name(self, call):
        self.add_grammar(call)
        return self.get_name(call.func)

    def visit_Name(self, name):
        self.add_grammar(name)
        if name.id in self.bindings:
            self.add_use(name.id)

async def code_to_module_uses(json_object):
    try:
        code = base64.b64decode(json_object['code'].encode('utf-8'))
        context = json_object['context']
        reference_collector = ReferenceCollector(context['private_modules'] if 'private_modules' in context else [])
        reference_collector.visit(ast.parse(code, filename = context['filename'] if 'filename' in context else '<unknown>'))
        data = { 'use_count': reference_collector.use_count }
    except KeyError as exc:
        data = { 'error': errno.EINVAL, 'message': str(exc) }
    except ValueError as exc:
        if exc.args[0].find('source code string cannot contain null bytes') >= 0:
            LOGGER.error('Skipping parsing because code contains null bytes!')
            data = { 'error': errno.EPERM, 'message': str(exc) }
        else:
            LOGGER.exception('Unhandled exception!')
            data = { 'error': errno.EIO, 'message': str(exc) }
    except SyntaxError as exc:
        LOGGER.debug('%s => %s', exc, exc.text)
        data = { 'error': errno.EIO, 'message': str(exc) }
    except Exception as exc:
        LOGGER.exception('Unhandled exception')
        data = { 'error': errno.EIO, 'message': str(exc) }
    return json.dumps(data)


if __name__ == '__main__':
    AsyncTcpCallbackServer('0.0.0.0', 25252, code_to_module_uses, memoized = False).run()


