import time
import types
from functools import partial

from facade import Context
from promise import Promise

from log import get_console, get_callable_representation

console = get_console(format='{message}')

unwind_console = get_console(format='<light-yellow>unwind</light-yellow>{message}')


def unwind(generator, on_success, on_exceptions, to_generator=None, method='send'):
    """Подписывается на события с помощью промисов, затем возвращает состояние обратно генератору, либо возвращает из него значение"""
    unwind_console(f'(gen={generator}, on_success={get_callable_representation(on_success)}, fail={get_callable_representation(on_exceptions)}, to_generator={to_generator}, method={method})')

    try:
        # пробуем пнуть герератор
        returned = getattr(generator, method)(to_generator)
        unwind_console(f': complete send to generator, returned={returned}')

    except StopIteration as stop:
        unwind_console(f': StopIteration, return {get_callable_representation(on_success)}({stop.value})')

        return on_success(to_generator=stop.value) if on_success else None
    except Exception as exc:
        unwind_console(f': Exception, return {get_callable_representation(on_exceptions)}({exc})')

        return on_exceptions(to_generator=exc)

    if is_generator(returned):
        # generator вернул другой генератор

        unwind_console(f': to_generator is_generator')

        unwind(
            returned,
            on_success=partial(unwind, generator, on_success, on_exceptions),
            on_exceptions=partial(unwind, generator, on_success, on_exceptions, method='throw'),
        )
    elif is_promise(returned):
        unwind_console(': to_generator is_promise')

        returned.then(
            partial(unwind, generator, on_success, on_exceptions)
        ).catch(
            partial(unwind, generator, on_success, on_exceptions, method='throw')
        )
    else:
        unwind_console(': else')

        wait_all(
            returned,
            partial(unwind, generator, on_success, on_exceptions),
            partial(unwind, generator, on_success, on_exceptions, method='throw'),
        )


def wait_all(awaitables, on_success, fail):
    """Ждем всех, когда последний выполнится - затем снова пинаем генератор """

    counter = len(awaitables)

    def _do_resolve(to_generator):  # to_generator чтобы консистетно с остальными on_success
        """последний _do_resolve запустит on_success(results)"""
        nonlocal counter
        counter -= 1
        if counter == 0:
            on_success(None)


    for i, c in enumerate(awaitables):
        if is_generator(c):
            unwind(c, on_success=_do_resolve, on_exceptions=fail)
            continue

        if is_promise(c):
            c.then(
                _do_resolve
            ).catch(
                fail
            )
            continue

        raise Exception('Only promise or generator can be yielded to event loop')


def is_generator(val):
    return isinstance(val, types.GeneratorType)


def is_promise(val):
    return isinstance(val, Promise)


def hrtime():
    """high-resolution real time"""
    return int(time.time() * 10e6)


def sleep(duration) -> Promise:
    console(f'sleep({duration})')

    return Context.event_loop.set_timer(duration * 10e3)
