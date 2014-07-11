#!/usr/bin/env python3

import logging
import tornado.auth
import tornado.escape
import tornado.ioloop
import tornado.web
import os.path
import json

from tornado.concurrent import Future
from tornado import gen
from tornado.options import define, options, parse_command_line

define("port", default=8888, help="run on the given port", type=int)
define("debug", default=False, help="run in debug mode")
define("initial_word", default='耍寶', help="initial word")


class SrtrHistory(object):
    def __init__(self, initial_word):
        self.history = [initial_word]
        self.waiters = set()

    def last(self):
        return self.history[-1]

    def count(self):
        return len(self.history)

    def push(self, new_word):
        if self.last()[-1] != new_word[0]:
            return False
        self.history.append(new_word)
        for future in self.waiters:
            future.set_result((self.count(), self.last()))
        self.waiters.clear()
        return True

    def wait(self, position=None):
        future = Future()
        if position and position != self.count():
            future.set_result((self.count(), self.last()))
        else:
            self.waiters.add(future)
        return future

    def cancel_wait(self, future):
        self.waiters.remove(future)
        future.set_result((0, ''))

history = SrtrHistory(options.initial_word)


class BaseHandler(tornado.web.RequestHandler):
    pass


class MainHandler(BaseHandler):
    def get(self):
        self.write(json.dumps((history.count(), history.last())))


class NextWordHandler(BaseHandler):
    def get(self):
        word = self.get_argument('w')
        self.write(json.dumps(history.push(word)))


class UpdateHandler(BaseHandler):
    @gen.coroutine
    def get(self):
        position = self.get_argument('pos', None)
        self.future = history.wait(position=position)
        result = yield self.future
        if self.request.connection.stream.closed():
            return
        self.write(json.dumps(result))

    def on_connection_close(self):
        history.cancel_wait(self.future)


def main():
    parse_command_line()
    app = tornado.web.Application(
        [
            (r"/", MainHandler),
            (r"/next", NextWordHandler),
            (r"/update", UpdateHandler),
            ],
        template_path=os.path.join(os.path.dirname(__file__), "templates"),
        static_path=os.path.join(os.path.dirname(__file__), "static"),
        xsrf_cookies=True,
        debug=options.debug,
        )
    app.listen(options.port)
    tornado.ioloop.IOLoop.instance().start()


if __name__ == "__main__":
    main()
