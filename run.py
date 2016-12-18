import os
import ast
import json
import base64
import logging
import rsyslog

from collections import Counter
from multiprocessing import current_process

from asynctcp import AsyncTCPCallbackServer, run_simple_tcp_server, BlockingTCPClient

rsyslog.setup()
current_process().name = os.environ['HOSTNAME']

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

async def code_to_module_uses(code):
    try:
        uses = ReferenceCollector().visit(ast.parse(code))
        return json.dumps(uses)
    except SyntaxError as exc:
        LOGGER.info('Syntax error encountered...Rerouting to python2 parser: {}'.format(str(exc)))
        client = BlockingTCPClient('python_2_parser', 25253, encode = lambda d: base64.b64encode(d) + bytes('\n', 'utf-8'))
        uses = client.send(code).decode('utf-8')
        return uses 
    except Exception as exc:
        LOGGER.exception('Unhandled exception in python parser {}'.format(exc))
        return json.dumps(ReferenceCollector().noop())

if __name__ == '__main__':
    AsyncTCPCallbackServer(
            callback = code_to_module_uses, 
            host = '0.0.0.0',
            port = 25252,
            encode = lambda d: d.encode('utf-8'),
            decode = base64.b64decode
            ).run()
