from os import environ as env
import ast
import json
import errno
import base64
import logging
import rsyslog

from collections import Counter
from multiprocessing import current_process

from asynctcp import AsyncTcpCallbackServer


current_process().name = env['HOSTNAME'] if 'HOSTNAME' in env else 'python-parser'
rsyslog.setup(log_level=env['LOG_LEVEL'] if 'LOG_LEVEL' in env else 'DEBUG')


LOGGER = logging.getLogger()


class ReferenceCollector(ast.NodeVisitor):

    def __init__(self):
        super().__init__()
        self.bindings = dict()
        self.use_count = Counter()

    def visit(self, node):
        super().visit(node)
        self.use_count.update(['__grammar__'+node.__class__.__name__])
        return self.use_count

    def noop(self):
        return self.use_count

    def visit_Import(self, node):
        for alias in node.names:
            if alias.asname:
                self.bindings[alias.asname] = alias.name
            else:
                self.bindings[alias.name] = alias.name
            self.use_count.update([alias.name])

    def visit_ImportFrom(self, node):
        if node.level == 0:
            for alias in node.names:
                if alias.asname:
                    self.bindings[alias.asname] = node.module
                else:
                    self.bindings[alias.name] = node.module
                self.use_count.update([node.module])
        else:
            # relative import means private module
            pass

    def visit_Name(self, node):
        if node.id in self.bindings:
            self.use_count.update([self.bindings[node.id]])


async def code_to_module_uses(json_object):
    try:
        code = base64.b64decode(json_object['code'].encode('utf-8'))
        context = json_object['context']
        LOGGER.debug('Parsing %s/%s %s', context['commit'][:7]+'...', context['path'], context['order'])
        data = {
            'use_count': ReferenceCollector().visit(
                ast.parse(code, filename=context['path'])
            )
        }
    except KeyError as exc:
        data = { 'error': errno.EINVAL }
    except ValueError as exc:
        if exc.args[0].find('source code string cannot contain null bytes') >= 0:
            LOGGER.error('Skipping parsing because code contains null bytes!')
            data = { 'error': errno.EPERM }
        else:
            LOGGER.exception('Unhandled exception!')
            data = { 'error': errno.EIO }
    except SyntaxError as exc:
        LOGGER.debug('%s => %s', exc, exc.text)
        data = { 'error': errno.EIO }
    except Exception as exc:
        LOGGER.exception('Unhandled exception')
        data = { 'error': errno.EIO }
    return json.dumps(data)


if __name__ == '__main__':
    AsyncTcpCallbackServer('0.0.0.0', 25252, code_to_module_uses, memoized = False).run()


