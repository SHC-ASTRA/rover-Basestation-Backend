from util.websocket_types import types


async def main():
    print(f"\033[1m{'class':25s}type\033[0m")
    for t in types:
        print(f"{t.__name__:25s}{t.msg_type}")
