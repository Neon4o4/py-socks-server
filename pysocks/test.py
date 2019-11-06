from server import SocksServer


def main():
    server = SocksServer(addr=('127.0.0.1', 2468))
    server.start()


# main()
