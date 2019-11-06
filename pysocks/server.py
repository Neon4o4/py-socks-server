# -*- coding: utf-8 -*-
import threading
import socket
import signal
import select
import time

import net
import connector


class SocksServer:
    # SOCKS 5 PROTOCOL: https://www.ietf.org/rfc/rfc1928.txt
    METHOD_NO_AUTH = 0x00
    METHOD_PASSWD  = 0x02

    METHODS_SUPPORT = (METHOD_NO_AUTH,)

    SOCKS_VERSION = 5

    def __init__(self, addr=('0.0.0.0', 1080), max_conn=4096, sock_type=connector.TCPConnector):
        """
        :param addr: local address to bind
        :param max_conn: the maximum number of connections to handle
        :param connector: the 'socket' used to connect the remote, must be instance of Connector
        """
        if not issubclass(sock_type, connector.Connector):
            raise TypeError
        self._addr = addr
        self._max_conn = max_conn
        self._isRunning = False
        self._tcp_sock = None
        self._udp_sock = None
        self._cleaner = None
        self._threads = {}
        self._THREADS_LOCK = threading.Lock()

        addr_info = socket.getaddrinfo(*self._addr)
        if not addr_info:
            print('Cannot resolve local address')
            return
        self._sock_family, *_ = addr_info[0]  # use the default one

        signal.signal(signal.SIGTERM, self.exit)
        signal.signal(signal.SIGINT, self.exit)

    @staticmethod
    def handle(conn, local_addr):
        conn.settimeout(300)
        try:
            # authentication method negotiation
            ver, client_methods = net.auth_negotiate(conn)
            if ver != SocksServer.SOCKS_VERSION:
                conn.close()
                return
            use_method = None
            for m in SocksServer.METHODS_SUPPORT:
                if m in client_methods:
                    use_method = m
                    break
            if use_method is None:
                net.answer_auth_negotiate(conn, ver, 0xFF)  # no method selected
                conn.close()
                return
            net.answer_auth_negotiate(conn, ver, use_method)

            # cmd request
            ver, cmd, rsv, atype, addr, port = net.cmd(conn)
            if ver != SocksServer.SOCKS_VERSION:
                conn.close()
                return
            # determine address type
            addr_info = socket.getaddrinfo(addr, port)
            if not addr_info:
                # cannot connect
                conn.close()
                return
            sock_family, *_ = addr_info[0]  # use the default one
            # now connect
            remote_addr = (addr, port)
            remote = socket.socket(sock_family, socket.SOCK_STREAM)
            try:
                remote.connect(remote_addr)
            except TimeoutError as e:
                print('Remote connection timeout: %s, %s' % (str(remote_addr), str(e)))
                return
            bind_addr = remote.getsockname()
            if remote.family == socket.AF_INET:
                atype = 0x01  # ipv4
            elif remote.family == socket.AF_INET6:
                atype = 0x04  # ipv6
            else:
                raise ValueError('Unknown socket family')
            net.answer_cmd(conn, ver, cmd, atype, bind_addr)

            # and finally, data exchange
            while True:
                r, w, e = select.select([conn, remote], [], [])
                if conn in r:
                    data = conn.recv(1024)
                    if remote.send(data) <= 0:
                        break
                if remote in r:
                    data = remote.recv(1024)
                    if conn.send(data) <= 0:
                        break
        except socket.timeout as e:
            print('socket timeout: %s' % (str(e)))
        finally:
            conn.close()

    def start(self):
        self._isRunning = True
        if not self._tcp_sock:
            self._tcp_sock = socket.socket(self._sock_family, socket.SOCK_STREAM)
        self._tcp_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self._tcp_sock.bind(self._addr)
        self._tcp_sock.listen(self._max_conn)
        self._tcp_sock.settimeout(1)
        while self._isRunning:
            if len(self._threads) >= self._max_conn:
                if not self.clean_threads():
                    time.sleep(0)  # yield control
                    continue
            try:
                conn, addr = self._tcp_sock.accept()
                handling_thread = threading.Thread(target=self.handle, args=(conn, addr))
                self._THREADS_LOCK.acquire()
                self._threads[addr] = handling_thread
                self._THREADS_LOCK.release()
                handling_thread.setDaemon(True)
                handling_thread.start()
            except socket.timeout:
                continue
        self.clean_up()

    def exit(self, signum, frame):
        self._isRunning = False

    def clean_up(self):
        if self._tcp_sock:
            self._tcp_sock.close()
        if self._udp_sock:
            self._udp_sock.close()
        self.clean_threads()

    def clean_threads(self):
        cnt_cleaned = 0
        for k, t in list(self._threads.items()):
            if not t.isAlive():
                self._THREADS_LOCK.acquire()
                self._threads.pop(k)
                cnt_cleaned += 1
                self._THREADS_LOCK.release()
        return cnt_cleaned
