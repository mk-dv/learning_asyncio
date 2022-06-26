from promise import Promise
from taskqueue import TaskQueue
from utils import hrtime, is_generator, unwind

from log import get_console, get_callable_representation

console = get_console(format='<light-blue>EventLoop</light-blue>{message}')


class EventLoop:
    def __init__(self):
        self._queue = TaskQueue()
        self._time = None

    def run(self, entry_point, *args):
        console(f'.run(entry_point={entry_point}, args={args}')

        self._execute(entry_point, *args)

        while not self._queue.is_empty():
            fn, mask = self._queue.pop(self._time)  # *mask
            self._execute(fn, mask)  # *mask

        self._queue.close()

    def register_fileobj(self, fileobj, callback):
        callback_str = get_callable_representation(callback)
        console(f'.register_fileobj(fileobj={fileobj}, callback={callback_str})')

        self._queue.register_fileobj(fileobj, callback)

    def unregister_fileobj(self, fileobj):
        console(f'.unregister_fileobj(fileobj={fileobj}')

        self._queue.unregister_fileobj(fileobj)

    def set_timer(self, duration):
        console(f'.set_timer(duration={duration})')

        p = Promise()
        self._time = hrtime()

        self._queue.register_timer(self._time + duration,
                                   p._resolve)
        return p

    def _execute(self, callback, *args):
        callback_str = get_callable_representation(callback)
        console(f'._execute(callback={callback_str}, args={args}')

        # self._time = hrtime()  # по идее не нужно

        try:
            returned = callback(*args)

            if is_generator(returned):
                unwind(
                    generator=returned,
                    on_success=None,
                    on_exceptions=lambda e: print('Uncaught rejection:', e),
                )
        except Exception as exc:
            print('Uncaught exception:', exc)

        self._time = hrtime()
        console(f'._execute end')
