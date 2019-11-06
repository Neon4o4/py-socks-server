from pysocks import SocksServer


def main():
    server = SocksServer(addr=('0.0.0.0', 2468))
    server.start()


main()
