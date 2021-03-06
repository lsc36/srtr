#!/usr/bin/env python3

import logging
import tornado.auth
import tornado.escape
import tornado.ioloop
import tornado.web
import tornado.escape
import os.path
import json

from tornado.concurrent import Future
from tornado import gen
from tornado.options import define, options, parse_command_line

define("port", default=8888, help="run on the given port", type=int)
define("debug", default=False, help="run in debug mode")
define("initial_word", default='耍寶', help="initial word")
define("reset", default=False, help="reset history (not reading previous save)")


class SrtrHistory(object):
    def __init__(self, initial_word):
        self.history = [initial_word]
        self.waiters = set()

    def last(self):
        return self.history[-1]

    def count(self):
        return len(self.history)

    def update(self):
        for future in self.waiters:
            future.set_result(dict(position=self.count(), last_word=self.last()))
        self.waiters.clear()

    def push(self, new_word):
        if len(new_word) > 32:
            return False
        if self.last()[-1] != new_word[0]:
            return False
        if new_word in self.history:
            return False
        self.history.append(new_word)
        self.update()
        return True

    def wait(self, position):
        future = Future()
        if position != self.count():
            future.set_result(dict(position=self.count(), last_word=self.last()))
        else:
            self.waiters.add(future)
        return future

    def cancel_wait(self, future):
        self.waiters.remove(future)
        future.set_result((0, ''))

    def save(self):
        f = open('history.json', 'w')
        f.write(json.dumps(self.history))
        f.close()

    def load(self):
        f = open('history.json', 'r')
        self.history = json.loads(f.read())
        f.close()
        self.update()

history = SrtrHistory(options.initial_word)


class BaseHandler(tornado.web.RequestHandler):
    pass


class MainHandler(BaseHandler):
    def get(self):
        self.render('index.html',
            position=history.count(), last_word=history.last())


class NextWordHandler(BaseHandler):
    def get(self):
        word = self.get_argument('w')
        self.write(json.dumps(history.push(word.strip())))


class UpdateHandler(BaseHandler):
    @gen.coroutine
    def get(self):
        position = int(self.get_argument('pos', None))
        self.future = history.wait(position=position)
        result = yield self.future
        if self.request.connection.stream.closed():
            return
        self.write(result)

    def on_connection_close(self):
        history.cancel_wait(self.future)


class HistoryHandler(BaseHandler):
    def get(self):
        self.render('history.html',
            history=reversed(list(zip(range(1, history.count() + 1), history.history))))


class RulesHandler(BaseHandler):
    def get(self):
        self.render('rules.html')


class SaveHandler(BaseHandler):
    def get(self):
        history.save()
        self.write('true')


class LoadHandler(BaseHandler):
    def get(self):
        history.load()
        self.write('true')


def main():
    parse_command_line()

    if options.reset:
        logging.info("History reset")
    else:
        try:
            history.load()
            logging.info("History loaded")
        except:
            logging.warning("Error loading history, starting from initial word")

    app = tornado.web.Application(
        [
            (r"/", MainHandler),
            (r"/next", NextWordHandler),
            (r"/update", UpdateHandler),
            (r"/history", HistoryHandler),
            (r"/rules", RulesHandler),
            (r"/save", SaveHandler),
            (r"/load", LoadHandler),
            ],
        template_path=os.path.join(os.path.dirname(__file__), "templates"),
        static_path=os.path.join(os.path.dirname(__file__), "static"),
        xsrf_cookies=True,
        debug=options.debug,
        )
    app.listen(options.port)
    try:
        tornado.ioloop.IOLoop.instance().start()
    except:
        pass
    finally:
        history.save()
        logging.info("History saved")


if __name__ == "__main__":
    main()
