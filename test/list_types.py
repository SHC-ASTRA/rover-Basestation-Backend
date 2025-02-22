from util.websocket_types import types

# ANSI escape codes for bold and reset
BOLD = "\033[1m"
END = "\033[0m"
GREEN = "\033[92m"
MAGENTA = "\033[95m"


async def main():
    for t in types:
        print(f'{BOLD}{t.__name__:22s}{END}{GREEN}"{t.msg_type}"{END}')
        spec = list(t.spec)
        spec.sort(key=lambda x: x.field)
        for entry in spec:
            print(f"  {entry.field:20s}{MAGENTA}{entry.field_type.__name__}{END}")
        print()
