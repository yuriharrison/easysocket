import sys
import traceback
import socket


# TODO: stop serve if it's not possible to bind
# to the given port


class EasySocket:
    ack_byte = b'\00'

    def __init__(self, server_ip, port, buffer_size=1024):
        self.server_ip, self.port = self.address = (server_ip, port)
        self.buffer_size = buffer_size

    def receive(self, data):
        pass


class EasySocketServer(EasySocket):
    serve = True

    def serve_forever(self):
        while self.serve:
            self._server()

    def _server(self):
        pass

    def stop_serve(self):
        self.serve = False


class TCPServer(EasySocketServer):
    receive_chunks = False

    def _server(self):
        try:
            conn = None
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.bind((self.server_ip, self.port))
            s.listen(5)
            conn, addr = s.accept()
            self.connection(addr)
            receive_chunks = conn.recv(1)
            full_data = b''
            while True:
                data = conn.recv(self.buffer_size)
                if not data: break
                if receive_chunks:
                    full_data += data
                else:
                    self.receive(data)
                    self.receive_all(data)

            if receive_chunks:
                self.receive_all(full_data)

            ack = b'\00'
            assert len(ack) == 1
            conn.sendall(ack)
        except:
            exc = sys.exc_info()
            traceback.print_exception(*exc)
        finally:
            if conn:
                conn.close()

    def connection(self, addr):
        pass

    def receive_all(self, data):
        pass


class UDPServer(EasySocketServer):

    def _server(self):
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.bind(self.address)
            data, addr = s.recvfrom(self.buffer_size)
            self.receive(addr, data)
        finally:
            s.close()

    def receive(self, addr, data):
        pass


class TCPClient(EasySocket):

    def __enter__(self):
        self.open_connection()
        self.connection.sendall(b'')

    def __exit__(self, *i):
        self.close_connection()

    def open_connection(self):
        self.connection = s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect(self.address)
        
    def close_connection(self):
        self.connection.close()
        self.connection = None

    def send(self, data):
        self.connection.sendall(data)

    def send_all(self, data):
        try:
            self.open_connection()
            self.connection.sendall(self.ack_byte)
            self.connection.sendall(data)
            self.connection.sendall(b'')
            self.connection.shutdown(1)
            try:
                ack = self.connection.recv(1)
                return ack
            except ConnectionResetError:
                pass
        finally:
            self.close_connection()


class UDPClient(EasySocket):
    
    def send(self, data, batch_size=None):
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        if batch_size:
            for chunk in self.chunks(data, batch_size):
                s.sendto(chunk, self.address)
        else:
            s.sendto(data, self.address)

    def chunks(self, data, batch_size):
        range_, mod = divmod(len(data), batch_size)
        range_ += 1 if mod else 0
        for i in range(range_):
            range_s, range_f = batch_size*i, batch_size*(i + 1)
            if i == range_ - 1:
                chunk = data[range_s:]
            else:
                chunk = data[range_s:range_f]
            yield chunk