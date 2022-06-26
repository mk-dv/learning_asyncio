from log import get_logger
from queue import Queue
from utils import hrtime

logger = get_logger(format='{message}')


class EventLoop:
    def __init__(self):
        logger.info('EventLoop.__init__()')

        self._queue = Queue()
        self._time = None

    def run(self, entry_point, *args):
        logger.info(f'EventLoop.run(entry_point={entry_point}, args={args}')

        self._execute(entry_point, *args)

        while not self._queue.is_empty():
            fn, *mask = self._queue.pop(self._time)  # берем последний добавленный колбек
            self._execute(fn, *mask)

        self._queue.close()

    def register_fileobj(self, fileobj, callback):
        logger.info(f'EventLoop.register_fileobj(fileobj={fileobj}, callback={callback})')

        self._queue.register_fileobj(fileobj, callback)

    def unregister_fileobj(self, fileobj):
        logger.info(f'EventLoop.unregister_fileobj(fileobj={fileobj}')

        self._queue.unregister_fileobj(fileobj)

    def set_timer(self, duration, callback):
        logger.info(f'EventLoop.set_timer(duration={duration}, callback={callback}')

        self._time = hrtime()
        logger.info(f'EventLoop.set_timer: EventLoop._time <- {self._time}')
        self._queue.register_timer(self._time + duration,
                                   callback)  # разобраться почему lambda нужна

    def _execute(self, callback, *args):
        logger.info(f'EventLoop._execute(callback={callback}, args={args}')

        self._time = hrtime()  # не думаю что это нужно
        logger.info(f'EventLoop._execute start: EventLoop._time <- {self._time}')
        try:
            logger.info(f'EventLoop._execute: trying execute {callback}(*{args})')
            # "корень" стека
            callback(*args)
        except Exception as exc:
            print('Uncaught exception:', exc)

        self._time = hrtime()
        logger.info(f'EventLoop._execute end: EventLoop._time <- {self._time}')
