from os import environ as env
import ast
import json
import base64
import logging
import rsyslog

from collections import Counter
from multiprocessing import current_process

from asynctcp import AsyncTCPCallbackServer, BlockingTCPClient


current_process().name = env['HOSTNAME']
rsyslog.setup(log_level=env['LOG_LEVEL'] if 'LOG_LEVEL' in env else 'DEBUG')


LOGGER = logging.getLogger()


class ReferenceCollector(ast.NodeVisitor):

    def __init__(self):
        super().__init__()
        self.bindings = dict()
        self.use_count = Counter()

    def visit(self, node):
        super().visit(node)
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
            # levels don't work when the filename given
            # to 'ast.parse' is unknown
            pass

    def visit_Name(self, node):
        if node.id in self.bindings:
            self.use_count.update([self.bindings[node.id]])


async def code_to_module_uses(code):
    try:
        uses = ReferenceCollector().visit(ast.parse(code))
        return json.dumps(uses)
    except SyntaxError as exc:
        LOGGER.debug('Syntax error encountered...Rerouting to python2 parser: {}'.format(str(exc)))
        client = BlockingTCPClient('python_2_parser', 25253, encode = lambda d: base64.b64encode(d) + bytes('\n', 'utf-8'))
        uses = client.send(code).decode('utf-8')
        return uses 
    except ValueError as exc:
        if exc.message.find('source code string cannot contain null bytes') >= 0:
            LOGGER.info('Skipping parsing because code contains null bytes!')
            return json.dumps(ReferenceCollector().noop())
        else:
            LOGGER.exception('Unhandled exception!')
            return json.dumps(ReferenceCollector().noop())
    except Exception as exc:
        LOGGER.exception('Unhandled exception')
        return json.dumps(ReferenceCollector().noop())


if __name__ == '__main__':
    AsyncTCPCallbackServer(
        callback = code_to_module_uses, 
        host = '0.0.0.0',
        port = 25252,
        encode = str.encode,
        decode = base64.b64decode
    ).run()
