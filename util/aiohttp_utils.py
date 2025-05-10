from aiohttp import web
from typing import *
import asyncio
import logging
import traceback

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
    _queue: asyncio.Queue = asyncio.Queue()

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

    async def send(self, msg: str):
        """
        Send a message to all handled websockets.

        :param msg: bytes
            The message to send.
        """
        await self._queue.put(msg)

    async def loop(self):
        """
        Main loop to send messages to all handled websockets.
        """
        while True:
            await self._send_all(await self._queue.get())

    async def _send_all(self, msg: str):
        """
        Send a message to all handled websockets.

        :param msg: bytes
            The message to send.
        """

        # LOG.debug(f"Sending WS message to {len(self._connections)} clients: {msg}")

        # send messages to all connections
        to_remove = set()
        for ws in self._connections:
            # if it's closed, keep track of it to remove it
            if ws.closed:
                to_remove.add(ws)
                continue
            try:
                await ws.send_str(msg, self.compress)
            except Exception as e:
                print(traceback.format_exc())
                LOG.error(f"Error sending message to {ws}: {e}")
                to_remove.add(ws)

        # remove closed connections
        for ws in to_remove:
            self.remove(ws)

    async def close(self):
        """
        Close all connections.
        """
        for ws in self._connections:
            await ws.close()
        self._connections.clear()
