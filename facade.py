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
