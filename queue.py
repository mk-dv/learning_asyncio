import collections
import heapq
import selectors
import time

from log import get_logger

logger = get_logger(format='{message}')


class Queue:
    """Фасад для двух суб-очередей"""
    def __init__(self):
        logger.info('Queue.__init__()')

        # мультиплексирование i/o
        self._selector = selectors.DefaultSelector()
        self._timers = []
        self._timer_no = 0
        self._ready = collections.deque()

    def register_timer(self, tick, callback):
        logger.info(f'Queue.register_timer(tick={tick}, callback={callback})')

        timer = (tick, self._timer_no, callback)
        heapq.heappush(self._timers, timer)
        self._timer_no += 1

    def register_fileobj(self, fileobj, callback):
        logger.info(f'Queue.register_fileobj(fileobj={fileobj}, callback={callback})')

        events = selectors.EVENT_READ | selectors.EVENT_WRITE
        # Зарегистрировать файловый объект для выбора, отслеживая его на предмет событий ввода-вывода.
        # fileobj — это файловый объект, который нужно отслеживать. Это может быть целочисленный файловый дескриптор или объект с методом fileno(). events — это побитовая маска отслеживаемых событий. data — непрозрачный объект.
        # Это возвращает новый экземпляр SelectorKey или вызывает ValueError в случае недопустимой маски события или дескриптора файла, или KeyError, если объект файла уже зарегистрирован
        self._selector.register(fileobj, events, callback)

    def unregister_fileobj(self, fileobj):
        logger.info(f'Queue.unregister_fileobj(fileobj={fileobj})')

        # Это возвращает связанный экземпляр SelectorKey или вызывает KeyError, если fileobj не зарегистрирован.
        self._selector.unregister(fileobj)

    def pop(self, tick):
        """Возвращает следующий готовый к выполению callback
        Если нечего запускать - просто спит

        На каждой итерации цикл событий пытается синхронно извлечь следующий обратный вызов из очереди. Если в данный
        момент нет обратного вызова для выполнения, pop() блокирует основной поток. Когда обратный вызов готов, цикл
        обработки событий выполняет его. Выполнение обратного вызова всегда происходит синхронно. Каждое выполнение
        обратного вызова запускает новый стек вызовов, который длится до полного синхронного вызова в дереве вызовов с
        корнем в исходном обратном вызове. Это также объясняет, почему ошибки должны доставляться как параметры
        обратного вызова, а не выбрасываться. Создание исключения влияет только на текущий стек вызовов, в то время
        как стек вызовов получателя может находиться в другом дереве. И в любой момент времени существует только один
        стек вызовов. т.е. если исключение, выброшенное функцией, не было перехвачено в текущем стеке вызовов, оно
        появится непосредственно в методе EventLoop._execute().

        Выполнение текущего обратного вызова регистрирует новые обратные вызовы в очереди. И цикл повторяется.
        """
        logger.info(f'Queue.pop(tick={tick})')

        if self._ready:
            queue_element = self._ready.popleft()
            logger.info(f'Queue.pop:Queue._ready not empty -> return {queue_element}')
            return queue_element

        timeout = self.get_timeout(tick)
        logger.info(f'timeout={timeout}')

        # при операциях на зареганых сокетах - возникает event соответствующей
        # маской и данными
        events = self.select(timeout)
        logger.info(f'events={events}')

        if events:
            logger.info('Queue.pop appending events to _ready')
        else:
            logger.info('Queue.pop No events')

        for key, mask in events:
            callback = key.data
            self._ready.append((callback, mask))

        if events:
            logger.info(f'Queue._ready={self._ready}')

        # нет готовых, но есть таймеры -> спим до ближайшего и возвращаем его
        if not self._ready and self._timers:
            idle = (self._timers[0][0] - tick)

            logger.info(f'Queue._ready is empty, _timers={self._timers}')

            # если до следующего события срабатывающего по таймеру времени меньше чем тика оно считается следующим, иначе засыпаем
            if idle > 0:
                logger.info(f'Queue.pop sleeping for {idle / 10e6}')
                time.sleep(idle / 10e6)

                logger.info(f'recursive call Queue.pop')
                queue_element = self.pop(tick + idle)

                logger.info(f'Queue.pop returning {queue_element}')
                return queue_element

        # if ближайший таймер в пределах тика
        while self._timers and self._timers[0][0] <= tick:
            logger.info(f'Queue._timers={self._timers}\n\t\t, Qeueu._timers[0][0] <= {tick}')

            *_, callback = heapq.heappop(self._timers)

            logger.info(f'Queue.pop append {callback} to _ready')
            self._ready.append((callback,))

        logger.info(f'Queue.pop reach the bottom, Queue._ready={self._ready}')
        result = self._ready.popleft()

        logger.info(f'Queue._ready.popleft()={result}')
        return result

    def select(self, timeout):
        logger.info(f'Queue.select(timeout={timeout})')

        try:
            """Берем первый готовый сокет"""

            logger.info('Queue.select trying get event by timeout')
            events = self._selector.select(timeout)
        except OSError:
            logger.info(f'Qeue.select error - sleeping for {timeout}')

            time.sleep(timeout)
            events = tuple()

        return events

    def get_timeout(self, tick):
        logger.info(f'Queue.get_timeout(tick={tick})')
        return (self._timers[0][0] - tick) / 10e6 if self._timers else None

    def is_empty(self):
        # .get_map Возвращает сопоставление файловых объектов с ключами селектора.
        return not (self._ready or self._timers or self._selector.get_map())

    def close(self):
        self._selector.close()