from aiohttp import web
from typing import *


def file_route(table: web.RouteTableDef, route: str, path: str):
    """Registers a route to serve a file"""
    print(f"registered file route {route} -> {path}")

    @table.get(route)
    def _inner(_: web.BaseRequest) -> web.FileResponse:
        return web.FileResponse(path)


class WSHandler:
    _connections: Set[web.WebSocketResponse] = set()

    def __init__(self, compress: Optional[int] = None):
        self.compress = compress

    def add(self, ws: web.WebSocketResponse):
        self._connections.add(ws)

    def remove(self, ws: web.WebSocketResponse):
        try:
            self._connections.remove(ws)
        except KeyError:
            pass

    async def send(self, msg: bytes):
        to_remove = set()
        for ws in self._connections:
            if ws.closed:
                to_remove.add(ws)
                continue

            await ws.send_bytes(msg, self.compress)

        for ws in to_remove:
            self.remove(ws)
