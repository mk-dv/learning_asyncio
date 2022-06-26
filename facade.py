from log import get_logger

logger = get_logger(format='{message}')


class Context:
    """Context class is an execution context, providing a placeholder for
     the event loop reference"""

    class states:  # noqa
        INITIAL = 0
        CONNECTING = 1
        CONNECTED = 2
        CLOSED = 3

    @classmethod
    def set_event_loop(cls, event_loop):
        cls.event_loop = event_loop


class set_timer(Context):
    def __init__(self, duration, callback):
        """Convenience method to call event_loop.set_timer() without knowing about
         the current event loop variable
         регистрирует callback с задержкой в event loop

         duration is in microseconds

        """
        logger.info(f'set_timer.__init__(duration={duration}, callback={callback}')

        self.event_loop.set_timer(duration, callback)