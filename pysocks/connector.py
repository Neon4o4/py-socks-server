# -*- coding: utf-8 -*-
import socket


class Connector:
    def __init__(self, remote_addr):
        """
        Initialization
        :param remote_addr: remote address to connect
        """
        pass

    def connect(self):
        """
        Connect the remote server
        :return:
        """
        raise NotImplementedError

    def close(self):
        """
        Close the connection
        :return:
        """
        raise NotImplementedError

    def send(self, data):
        """
        Send data
        :param data:
        :return:
        """
        raise NotImplementedError

    def recv(self, length):
        """
        Receive data
        :param length:
        :return:
        """
        raise NotImplementedError

    def getsockinfo(self):
        """
        Get protocol family and socket name
        :return: sock_family, socket_name
        """
        raise NotImplementedError


class TCPConnector(Connector):
    def __init__(self, remote_addr):
        super().__init__(remote_addr)
        self._remote_addr = remote_addr
        remote_info = socket.getaddrinfo(*remote_addr)
        if not remote_info:
            raise socket.error('Cannot resolve address %s' % str(remote_addr))
        self._sock_family, *_ = remote_info[0]  # use the default one
        self._sock = socket.socket(self._sock_family, socket.SOCK_STREAM)

    def connect(self):
        if self._sock:
            raise RuntimeError('Duplicated connection')
        self._sock.connect(self._remote_addr)

    def close(self):
        if self._sock:
            self._sock.close()

    def send(self, data):
        self._sock.sendall(data)

    def recv(self, length):
        return self._sock.recv(length)

    def getsockinfo(self):
        return self._sock_family, self._sock.getsockname()

