import os
import ast
import json
import errno
import base64
import logging
import rsyslog

from collections import Counter
from multiprocessing import current_process

from asynctcp import AsyncTcpCallbackServer

current_process().name = os.environ['HOSTNAME']
rsyslog.setup(log_level = os.environ['LOG_LEVEL'])

LOGGER = logging.getLogger()

class ReferenceCollector(ast.NodeVisitor):

    def __init__(self):
        super().__init__()
        self.use_count = Counter()

    def __add_to_counter(self, name, allow_unrecognized = True):
        if allow_unrecognized or name in self.use_count:
            self.use_count.update([ name ])

    def visit(self, node):
        super().visit(node)
        return self.use_count

    def noop(self):
        return self.use_count

    def visit_Import(self, node):
        for name in node.names:
            self.__add_to_counter(name.asname or name.name)

    def visit_ImportFrom(self, node):
        self.__add_to_counter(node.module)

    def visit_Name(self, node):
        self.__add_to_counter(node.id, allow_unrecognized = False)

async def code_to_module_uses(json_object):
    try:
        code = base64.b64decode(json_object['code'].encode('utf-8'))
        data = { 'use_count': ReferenceCollector().visit(ast.parse(code)) }
    except KeyError as exc:
        data = { 'error': errno.EINVAL, 'use_count': {} }
    except ValueError as exc:
        if exc.args[0].find('source code string cannot contain null bytes') >= 0:
            LOGGER.error('Skipping parsing because code contains null bytes!')
            # with open('myexamplefile.py', 'wb') as f:
            #     f.write(code)
            data = { 'error': errno.EPERM, 'use_count': {} }
        else:
            LOGGER.exception('Unhandled exception!')
            data = { 'error': errno.EIO, 'use_count': {} }
    except SyntaxError as exc:
        LOGGER.warning('Invalid Python3 code received: ' + str(exc.msg))
        data = { 'error': errno.EIO, 'use_count': {} }
    except Exception as exc:
        LOGGER.exception('Unhandled exception')
        data = { 'error': errno.EIO, 'use_count': {} }
    return json.dumps(data)

if __name__ == '__main__':
    AsyncTcpCallbackServer('0.0.0.0', 25252, code_to_module_uses, memoized = False).run()