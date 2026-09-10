try:
    import queue
    import random
    import time
    from typing import Dict, Optional, Tuple
except ImportError as IE:
    raise IE

# In-memory registry mapping (host, port) tuples to listening OfflineSockets
_SERVER_REGISTRY: Dict[Tuple[str, int], "OfflineSocket"] = {}

AF_INET = 2
SOCK_STREAM = 1
SOL_SOCKET = 1
SO_REUSEADDR = 2

class OfflineSocket:
    # Standard socket constants for drop-in compatibility
    AF_INET = 2
    SOCK_STREAM = 1
    SOL_SOCKET = 1
    SO_REUSEADDR = 2

    def __init__(
        self,
        family: int = AF_INET,
        type: int = SOCK_STREAM,
        proto: int = 0,
        fileno=None,
    ):
        self.family = family
        self.type = type
        self.proto = proto

        self._address: Optional[Tuple[str, int]] = None
        self._peer_address: Optional[Tuple[str, int]] = None
        self._peer_socket: Optional["OfflineSocket"] = None

        self._incoming_conn_queue: Optional[queue.Queue] = None
        self._inbound_data_queue: queue.Queue = queue.Queue()
        self._buffer = bytearray()
        self._is_closed = False

        self._timeout = None

    def setsockopt(self, level: int, optname: int, value: int):
        """No-op stub to preserve compatibility with standard socket options."""
        pass

    def bind(self, address: Tuple[str, int]):
        """Binds the simulated socket to a local address tuple (host, port)."""
        self._address = address

    def listen(self, backlog: int = 5):
        """Registers the socket as a listening server in the shared memory registry."""
        if not self._address:
            raise OSError("Socket must be bound before calling listen()")
        self._incoming_conn_queue = queue.Queue(maxsize=backlog)
        _SERVER_REGISTRY[self._address] = self

    def accept(self) -> Tuple["OfflineSocket", Tuple[str, int]]:
        """Blocks until a simulated client connects, returning (server_end_socket, client_addr)."""
        if self._incoming_conn_queue is None:
            raise OSError("Socket is not listening")

        try:
            client_sock, client_addr = self._incoming_conn_queue.get(block=True, timeout=self._timeout)
            return client_sock, client_addr
        except queue.Empty:
            raise TimeoutError("accept() timed out")

    def settimeout(self, timeout: float):
        self._timeout = timeout

    def connect(self, address: Tuple[str, int]):
        """Connects to a listening server socket in the local registry."""
        if address not in _SERVER_REGISTRY:
            raise ConnectionRefusedError(f"No server listening on {address}")

        server_listener = _SERVER_REGISTRY[address]

        # Generate a simulated client address
        simulated_port = random.randint(49152, 65535)
        self._address = ("127.0.0.1", simulated_port)
        self._peer_address = address

        # Create server-side endpoint for this client
        server_end = OfflineSocket(self.family, self.type)
        server_end._address = address
        server_end._peer_address = self._address

        # Pair endpoints
        self._peer_socket = server_end
        server_end._peer_socket = self

        # Dispatch connection to server's accept queue
        server_listener._incoming_conn_queue.put((server_end, self._address))

    def send(self, data: bytes) -> int:
        """Sends data bytes to the paired remote socket."""
        self.sendall(data)
        return len(data)

    def sendall(self, data: bytes):
        """Enqueues data bytes into the connected peer's inbound queue."""
        if self._is_closed or not self._peer_socket:
            raise OSError("Socket is not connected")
        self._peer_socket._inbound_data_queue.put(bytes(data))

    def recv(self, bufsize: int = 1024) -> bytes:
        """Blocks until data is received from the peer, returning up to `bufsize` bytes."""
        if self._is_closed and not self._buffer:
            return b""

        while len(self._buffer) == 0:
            data = self._inbound_data_queue.get()
            if data is None:  # Sentinel for EOF/Peer connection closed
                return b""
            self._buffer.extend(data)

        chunk = bytes(self._buffer[:bufsize])
        del self._buffer[:bufsize]
        return chunk

    def close(self):
        """Closes the socket and notifies the connected peer."""
        if not self._is_closed:
            self._is_closed = True

            # Unregister server if applicable
            if self._address in _SERVER_REGISTRY:
                if _SERVER_REGISTRY[self._address] is self:
                    del _SERVER_REGISTRY[self._address]

            # Signal EOF to peer socket
            if self._peer_socket and not self._peer_socket._is_closed:
                self._peer_socket._inbound_data_queue.put(None)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()


# Alias class so callers can use `from OfflineSocket import socket`
socket = OfflineSocket
timeout = TimeoutError

if __name__ != '__main__':
    print("WARNING: OFFLINE SOCKET IMPORTED")
else:
    raise NotImplementedError("ERROR: STANDALONE NOT IMPLEMENTED")