# -*- coding: utf-8 -*-
import struct
import socket

__all__ = [
    'auth_negotiate',
    'answer_auth_negotiate',
    'cmd',
    'answer_cmd',
    # 'request',
    # 'answer_request'
]


# SOCKS 5 PROTOCOL: https://www.ietf.org/rfc/rfc1928.txt

def auth_negotiate(conn):
    header = conn.recv(2)
    version, n_method = struct.unpack('!BB', header)
    methods = []
    for _ in range(n_method):
        m = conn.recv(1)
        m, = struct.unpack('!B', m)
        methods.append(m)
    return version, methods


def answer_auth_negotiate(conn, version, method):
    data = struct.pack('!BB', version, method)
    conn.sendall(data)


def cmd(conn):
    data = conn.recv(4)
    version, cmd, rsv, atype = struct.unpack('!BBBB', data)

    addr = ''
    if atype == 1:  # ipv4
        addr = conn.recv(4)
        addr = socket.inet_ntoa(addr)
    # elif address_type == 4:  # ipv6  TODO
    elif atype == 3:  # domain
        domain_length = conn.recv(1)
        domain_length = ord(domain_length)
        addr = conn.recv(domain_length)
        addr = addr.decode('utf-8')

    port = conn.recv(2)
    port, = struct.unpack('!H', port)

    return version, cmd, rsv, atype, addr, port


def answer_cmd(conn, ver, cmd, atype, bind_addr):
    addr, port = bind_addr
    reply = ''
    if cmd == 1:  # connect
        addr, = struct.unpack("!I", socket.inet_aton(addr))
        reply = struct.pack("!BBBBIH", ver, 0, 0, atype, addr, port)
    conn.sendall(reply)
