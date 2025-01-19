from aiohttp import web
from typing import *
from google.protobuf.any_pb2 import Any as ProtoAny
import logging

LOG = logging.getLogger(__name__)


def file_route(table: web.RouteTableDef, route: str, path: str):
    """
    Registers a route to serve a file.

    :param table: web.RouteTableDef
        The route table to register the route with.
    :param route: str
        The route to register, e.g. "/api/file.txt".
    :param path: str
        The path to the file to serve.
    """
    LOG.info(f"registered file route {route} -> {path}")

    @table.get(route)
    def _inner(_: web.BaseRequest) -> web.FileResponse:
        return web.FileResponse(path)


class WSSender:
    """
    Handles sending messages to multiple websockets.

    :param compress: Optional[int]
        The compression level to use when sending messages.
    """

    _connections: Set[web.WebSocketResponse] = set()

    def __init__(self, compress: Optional[int] = None):
        self.compress = compress

    def add(self, ws: web.WebSocketResponse) -> bool:
        """
        Add a websocket to the handler pool.

        :param ws: web.WebSocketResponse
            Websocket to add.
        :return: bool
            True if the websocket was added, False if it was already in the pool.
        """
        if ws not in self._connections:
            self._connections.add(ws)
            return True
        return False

    def remove(self, ws: web.WebSocketResponse) -> bool:
        """
        Remove a websocket from the handler pool.

        :param ws: web.WebSocketResponse
            Websocket to remove.
        :return: bool
            True if the websocket was removed, False if it was not found.
        """
        try:
            self._connections.remove(ws)
            return True
        except KeyError:
            return False

    async def send(self, msg: ProtoAny):
        """
        Send a message to all handled websockets.

        :param msg: bytes
            The message to send.
        """

        msg_bytes = msg.SerializeToString()

        # send messages to all connections
        to_remove = set()
        for ws in self._connections:
            # if it's closed, keep track of it to remove it
            if ws.closed:
                to_remove.add(ws)
                continue

            await ws.send_bytes(msg_bytes, self.compress)

        # remove closed connections
        for ws in to_remove:
            self.remove(ws)
