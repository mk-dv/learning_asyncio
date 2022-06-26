from facade import Context

from log import get_callable_representation, get_console

console = get_console(format='<b><fg #F92672>Promise</fg #F92672></b>{message}')


class Promise(Context):
    """Способ привязки нескольких колбеков к вызову _resolve"""
    def __init__(self):
        self._on_resolve = []
        self._on_reject = []
        self._resolved = False
        self._rejected = False
        self._value = None


    # вроде это пока не используется
    # @classmethod
    # def all(cls, promises):
    #     console(f'.all({promises})')
    #
    #     pall = cls()
    #     counter = len(promises)
    #
    #     if counter == 0:
    #         pall._resolve()
    #         return pall
    #
    #     results = [None] * counter
    #
    #     def _on_single_resolved(i):
    #         def _callback(*args):
    #             nonlocal counter
    #
    #             results[i] = args
    #             counter -= 1
    #             if counter == 0:
    #                 pall._resolve(results)
    #
    #         return _callback
    #
    #     for idx, p in enumerate(promises):
    #         p.then(_on_single_resolved(idx))
    #         p.catch(pall._reject)
    #
    #     return pall

    def then(self, callback):
        callback_str = get_callable_representation(callback)
        console(f'.then(callback={callback_str})')

        if self._resolved:
            console(f'.then: self._resolved -> el._execute({callback_str}, *{self._value})')

            self.event_loop._execute(callback, *self._value)
        elif not self._rejected:
            console(f'.then: not self._rejected -> append {callback_str} to self._on_resolve')

            self._on_resolve.append(callback)
        return self

    def catch(self, callback):
        callback_str = get_callable_representation(callback)
        console(f'.catch(callback={callback_str}')

        if self._rejected:
            console(f'.catch: self._rejected -> el._execute({callback_str}, *{self._value}')

            self.event_loop._execute(callback, self._value)
        elif not self._resolved:
            console(f'.catch: not self._resolved -> append {callback_str} to self._on_reject')

            self._on_reject.append(callback)
        return self

    def _resolve(self, *args):
        console(f'._resolve(args={args})')

        if self._resolved or self._rejected:
            console(f"._resolve: {'resolved' if self._resolved else 'rejected'} -> return")

            return

        self._resolved = True
        self._value = args

        if self._on_resolve:  # debug
            console(f'._resolve: el._execute\n\t{self._on_resolve}')

        for callback in self._on_resolve:
            self.event_loop._execute(callback, *args)

    def _reject(self, error):
        if self._resolved or self._rejected:
            console(f"._reject: {'resolved' if self._resolved else 'rejected'} -> return")

            return

        self._rejected = True
        self._value = error

        if self._on_reject:  # debug
            console(f'._reject: run\n\t{self._on_reject}\n\t\t with error={error}')

        for callback in self._on_reject:
            callback(error)
