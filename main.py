import json
import random
import socket
import sys

from async_socket import async_socket
from event_loop import EventLoop
from facade import Context
from utils import sleep

from log import get_console

console = get_console(format='<bold>main</bold>{message}')

client_console = get_console(format='<bold>Client</bold>{message}')


class Client:
    def __init__(self, addr):
        self.addr = addr

    def get_user(self, user_id):
        client_console(f'.get_user(user_id={user_id})')

        return self._get(f'GET user {user_id}\n')

    def get_balance(self, account_id):
        client_console(f'.get_balance(account_id={account_id})')

        return self._get(f'GET account {account_id}\n')

    def _get(self, req):
        client_console(f'._get(req={req!r})')

        sock = async_socket(socket.AF_INET, socket.SOCK_STREAM)

        client_console('_get: start connetion')

        yield sock.connect(self.addr)

        client_console('._get: connect successful')

        try:
            client_console(f'._get: start sending {req.encode("utf8")}')

            yield sock.sendall(req.encode('utf8'))

            client_console(f'._get: sended, yield response')

            resp = yield sock.recv(1024)

            client_console(f'._get: requested response={resp}, returning')
            return json.loads(resp)
        finally:
            client_console('_get: closing socket')

            sock.close()


def get_user_balance(serv_addr, user_id):
    console(f'.get_user_balance(serv_addr={serv_addr}, user_id={user_id})')
    console('.get_user_balance sleeping')

    yield sleep(random.randint(0, 1000))

    client = Client(serv_addr)

    console(f'.get_user_balance: yield from client.get_user(user_id={user_id})')

    user = yield client.get_user(user_id)
    if user_id % 5 == 0:
        console('.get_user_balance: user_id % 5 -> raise Exception')

        raise Exception('It is OK to throw here')

    console(f'.get_user_balance: yield from client.get_balance({user["account_id"]})')

    acc = yield client.get_balance(user['account_id'])

    console('.get_user_balance returning value')

    return f'User {user["name"]} has {acc["balance"]} USD'


def print_balance(serv_addr, user_id):
    console(f'.print_balance(serv_addr={serv_addr}, user_id={user_id})')

    try:
        console(f'.print_balance: yield get_user_balance({serv_addr}, {user_id})')

        balance = yield get_user_balance(serv_addr, user_id)
        print(balance)
        # sys.exit()  # debug
    except Exception as exc:
        print('Catched:', exc)


def main1(serv_addr):
    console(f'.main1({serv_addr}')

    def on_sleep():
        console('.main1.on_sleep()')

        b = yield get_user_balance(serv_addr, 1)
        print('side flow:', b)  # <- до сюда вроде не доходит...

    # promise = sleep(5000)
    # promise.then(on_sleep)
    # sleep(5000).then(on_sleep)

    tasks = []
    for i in range(10):
        tasks.append(print_balance(serv_addr, i))
    # использование здесь yield from позволило бы избавиться от wait_all, и блок else в unwind
    yield tasks


def main2(*args):
    sock = async_socket(socket.AF_INET, socket.SOCK_STREAM)
    yield sock.connect(('info.cern.ch', 80))

    try:
        yield sock.sendall(b'GET / HTTP/1.1\r\nHost: info.cern.ch\r\n\r\n')
        val = yield sock.recv(1024)
        print(f'\n\n{val}\n\n')
    finally:  # позволяет закрывать сокет при выходе из функции
        sock.close()


if __name__ == '__main__':
    print('Run main1()')
    event_loop = EventLoop()
    Context.set_event_loop(event_loop)

    serv_addr = ('127.0.0.1', 53210)
    event_loop.run(main1, serv_addr)

    print('\nRun main2()')
    event_loop = EventLoop()
    Context.set_event_loop(event_loop)
    event_loop.run(main2)
