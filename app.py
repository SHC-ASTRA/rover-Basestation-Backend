#!/bin/env python

from aiohttp import web

routes = web.RouteTableDef()


@routes.get("/api")
async def handle(_):
    text = "Hello, world!"
    return web.Response(text=text)


app = web.Application()
app.add_routes(routes)

if __name__ == "__main__":
    web.run_app(app)
