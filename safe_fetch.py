import socket
from collections.abc import Callable

import requests
from requests.adapters import HTTPAdapter
from urllib3.connection import HTTPConnection, HTTPSConnection
from urllib3.connectionpool import HTTPConnectionPool, HTTPSConnectionPool

from url_safety import is_public_address

AddressPolicy = Callable[[str], bool]


class BlockedAddressError(OSError):
    pass


def _check_peer(sock: socket.socket, is_allowed: AddressPolicy) -> socket.socket:
    peer_address = sock.getpeername()[0]
    if not is_allowed(peer_address):
        sock.close()
        raise BlockedAddressError(
            f"refusing to connect to non-public address {peer_address}"
        )
    return sock


def _guarded_pool_classes(
    is_allowed: AddressPolicy,
) -> dict[str, type[HTTPConnectionPool]]:
    # The check runs on the socket actually connected, so redirects and DNS rebinding cannot skip it.
    class GuardedHTTPConnection(HTTPConnection):
        def _new_conn(self) -> socket.socket:
            return _check_peer(super()._new_conn(), is_allowed)

    class GuardedHTTPSConnection(HTTPSConnection):
        def _new_conn(self) -> socket.socket:
            return _check_peer(super()._new_conn(), is_allowed)

    class GuardedHTTPConnectionPool(HTTPConnectionPool):
        ConnectionCls = GuardedHTTPConnection

    class GuardedHTTPSConnectionPool(HTTPSConnectionPool):
        ConnectionCls = GuardedHTTPSConnection

    return {"http": GuardedHTTPConnectionPool, "https": GuardedHTTPSConnectionPool}


class _GuardedAdapter(HTTPAdapter):
    def __init__(self, is_allowed: AddressPolicy) -> None:
        self._is_allowed = is_allowed
        super().__init__()

    def init_poolmanager(self, *args, **kwargs) -> None:
        super().init_poolmanager(*args, **kwargs)
        self.poolmanager.pool_classes_by_scheme = _guarded_pool_classes(
            self._is_allowed
        )


def guarded_session(is_allowed: AddressPolicy = is_public_address) -> requests.Session:
    session = requests.Session()
    # An environment proxy would make the proxy, not the target, the peer that gets checked.
    session.trust_env = False
    adapter = _GuardedAdapter(is_allowed)
    session.mount("http://", adapter)
    session.mount("https://", adapter)
    return session
