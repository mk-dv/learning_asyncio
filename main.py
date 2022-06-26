import random
import socket
import time

from event_loop import async_socket, EventLoop
from facade import Context, set_timer


def get():
    sock = async_socket(socket.AF_INET, socket.SOCK_STREAM)

    job1 = sock.connect(('info.cern.ch', 80))
    # теперь нужно как-то привязать коллбек срабатывающий при коннекте и
    # вернуть управление el до завершения подключения

    # теперь мы можем выбрасывать эксепшены прямо наверх
    try:
        job2 = sock.sendall(b'GET / HTTP/1.1\r\nHost: info.cern.ch\r\n\r\n')
        # привязать колбек при отправке и вернуть управление

        job3 = sock.recv(1024)
        # аналогично
        print(job3.value)
    finally:
        sock.close()


def main():
    # 1: 1.62
    # 10: 1.17 - погрешность!
    for i in range(10):
        set_timer(random.randint(0, 10e6), get)


if __name__ == '__main__':
    event_loop = EventLoop()
    Context.set_event_loop(event_loop)
    start_time = time.perf_counter()
    event_loop.run(main)
    print('Elapsed: %s' % (time.perf_counter() - start_time))
