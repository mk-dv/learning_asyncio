# селекторы - высокоуровневая облочка для мультиплексирования
import selectors
import socket

import errno

from facade import Context
from log import get_logger

logger = get_logger(format='{message}')


class async_socket(Context):
    """Обертка на сокетом, регистрируем ?базовый файловый дескриптор неблокирующего сокета
    При появлении информации в файловом дескрипторе(видимо при <os>.send(descriptor) -> info)
    need read
    all data writen
    error occured
    -> el будет вызывать соответствующий callback
    """
    def __init__(self, *args):
        logger.info(f'async_socket.__init__(args={args})')

        self._sock = socket.socket(*args)
        self._sock.setblocking(False)
        self.event_loop.register_fileobj(self._sock, self._on_event)

        self._state = self.states.INITIAL
        self._callbacks = {}

    def connect(self, addr, callback):
        logger.info(f'async_socket.connect(addr={addr}, callback={callback}')

        if self._state != self.states.INITIAL:
            raise Exception(f'state {self.states.INITIAL} expected, but is {self._state}')

        self._state = self.states.CONNECTING
        self._callbacks['conn'] = callback

        # ~ connect, но -> код ошибки вместо возбуждения исключения
        error_code = self._sock.connect_ex(addr)
        if errno.errorcode[error_code] != 'EINPROGRESS':
            # неожиданное поведение - коннект возвращает не establishing connection in progress
            raise Exception('error code is not EINPROGRESS')

    def recv(self, n, callback):
        """

        Args:
            n (int): число байт
            callback:

        Returns: None
        """
        logger.info(f'async_socket.recv(n={n}, callback={callback}')

        if self._state != self.states.CONNECTED:
            Exception(f'socket.recv(): self._state expected 2 but actual is {self._state}')

        if 'recv' in self._callbacks:
            Exception('socket.recv(): recv in self._callbacks')

        def _on_read_ready(error):
            if error:
                return callback(error)
            data = self._sock.recv(n)
            callback(None, data)

        self._callbacks['recv'] = _on_read_ready

    def sendall(self, data, callback):
        logger.info(f'async_socket.sendall(data={data}, callback={callback}')

        if self._state != self.states.CONNECTED:
            raise Exception(f'socket.sendall(), self._state expected 2 but actual is {self._state}')

        if 'sent' in self._callbacks:
            raise Exception('socket.sendall(), sent in self._callbacks')

        def _on_write_ready(error):
            nonlocal data
            if error:
                return callback(error)

            n = self._sock.send(data)
            if n < len(data):
                data = data[n:]
                self._callbacks['sent'] = _on_write_ready
            else:
                callback(None)

        self._callbacks['sent'] = _on_write_ready

    def close(self):
        self.event_loop.unregister_fileobj(self._sock)
        self._callbacks.clear()
        self._state = self.states.CLOSED
        self._sock.close()

    def _on_event(self, mask):
        """run a callback from self._callbaks if exists"""
        logger.info(f'async_socket._on_event(mask={mask})')

        if self._state == self.states.CONNECTING:
            logger.info('async_socket._on_event: CONNECTING')
            if mask != selectors.EVENT_WRITE:
                raise Exception(
                    f'_on_event(): mask {selectors.EVENT_WRITE} expeted, but {mask} is actual'
                )

            callback = self._callbacks.pop('conn')

            error = self._get_sock_error()
            logger.info(f'async_socket._on_event -> _get_sock_error() = {error}')

            if error:
                self.close()
            else:
                self._state = self.states.CONNECTED
            callback(error)

        if mask & selectors.EVENT_READ:
            callback = self._callbacks.get('recv')
            if callback:
                del self._callbacks['recv']
                error = self._get_sock_error()
                callback(error)

        if mask & selectors.EVENT_WRITE:
            callback = self._callbacks.get('sent')
            if callback:
                del self._callbacks['sent']
                error = self._get_sock_error()
                callback(error)

    def _get_sock_error(self):
        """
        Флаги могут существовать на нескольких уровнях протоколов; они всегда присутствуют на самом верхнем из них.
        При манипулировании флагами сокета должен быть указан уровень, на котором находится этот флаг, и имя этого
        флага. Для манипуляции флагами на уровне сокета level задается как SOL_SOCKET. Для манипуляции флагами на
        любом другом уровне этим функциям передается номер соответствующего протокола, управляющего флагами.
        Например, для указания, что флаг должен интерпретироваться протоколом TCP, в параметре level должен
        передаваться номер протокола TCP;
        В случае успеха возвращается ноль.При ошибке возвращается - 1, а значение errno устанавливается должным
        образом.

        Returns: ConnectionError | None

        """
        logger.info('async_socket._get_sock_error()')

        errorno = self._sock.getsockopt(socket.SOL_SOCKET, socket.SO_ERROR)
        if errorno:
            return ConnectionError(
                f'connection failed: error: {errorno}, {errno.errorcode[errorno]}'
            )