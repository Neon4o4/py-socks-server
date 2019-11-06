# py-socks-server
A simple socks proxy server implemented in Python

## Usage
```python
from pysocks import SocksServer

server = SocksServer(('0.0.0.0', 2468))
server.start()
```
See `tests/test_main.py` for example.

## TODO
- ~Basic TCP support~ √
- UDP support
- IPv6 support
