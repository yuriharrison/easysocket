"""easysocket test unit"""
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../'))

import time
import traceback
import re
from threading import Thread

import pytest

from easysocket import EasySocket, TCPServer, UDPServer, TCPClient, UDPClient


ADDRESS = SERVER_IP, SERVER_PORT = ('127.0.0.1', 50550)
INVALID_PORT = 55500
DEFAULT_BUFFER_SIZE = 1024
REGEX_IP_ADDRESS = '^(([0-9]|[1-9][0-9]|1[0-9]{2}|2[0-4][0-9]|25[0-5])\.){3}([0-9]|[1-9][0-9]|1[0-9]{2}|2[0-4][0-9]|25[0-5])$'
TEST_DATA = ' '.join([str(i) for i in range(1000)]).encode()
STOP_SERVE_COMMAND = b'stop_serve'
THREAD_IS_DEAD = False

assert INVALID_PORT is not SERVER_PORT
assert re.match(REGEX_IP_ADDRESS, SERVER_IP)
assert len(STOP_SERVE_COMMAND) < DEFAULT_BUFFER_SIZE


class MyTCPServer(TCPServer):

    def connection(self, addr):
        try:
            ip, port = addr
            assert re.match(REGEX_IP_ADDRESS, ip)
            assert type(port) is int
        except:
            self.stop_serve()

    def receive_all(self, data):
        try:
            if data == STOP_SERVE_COMMAND:
                self.stop_serve()
            else:
                assert data == TEST_DATA
        except:
            self.stop_serve()


class MyUDPServer(UDPServer):

    def receive(self, addr, data):
        try:
            ip, port = addr
            assert re.match(REGEX_IP_ADDRESS, ip)
            assert type(port) is int

            if data == STOP_SERVE_COMMAND:
                self.stop_serve()
        except:
            self.stop_serve()


def test_ack_byte():
    assert len(EasySocket.ack_byte) == 1


def test_tcp():
    def start_tcp_server():
        global THREAD_IS_DEAD
        try:
            MyTCPServer(*ADDRESS).serve_forever()
            THREAD_IS_DEAD = True
        except:
            exc = sys.exc_info()
            traceback.print_exception(*exc)

    global THREAD_IS_DEAD
    THREAD_IS_DEAD = False
    Thread(target=start_tcp_server, name='test_tcp_server').start()
    
    conn = TCPClient(*ADDRESS)
    conn.send_all(TEST_DATA)
    with conn:
        conn.send(STOP_SERVE_COMMAND)
    with pytest.raises(ConnectionRefusedError):
        TCPClient(SERVER_IP, INVALID_PORT).open_connection()
    assert THREAD_IS_DEAD


def test_udp():
    def start_udp_server():
        global THREAD_IS_DEAD
        try:
            MyUDPServer(*ADDRESS).serve_forever()
            THREAD_IS_DEAD = True
        except:
            exc = sys.exc_info()
            traceback.print_exception(*exc)

    global THREAD_IS_DEAD
    THREAD_IS_DEAD = False
    Thread(target=start_udp_server, name='test_udp_server').start()

    conn = UDPClient(*ADDRESS)
    conn.send(TEST_DATA, batch_size=DEFAULT_BUFFER_SIZE)
    
    # Sends a command to stop the UDP server every .3 second,
    # in case of any package get lost. It gives a maximum of
    # 2 seconds to close the service.
    start_time = time.time()
    while not THREAD_IS_DEAD:
        conn.send(STOP_SERVE_COMMAND)
        if (time.time() - start_time) > 2: break
        time.sleep(.3)
    assert THREAD_IS_DEAD
        