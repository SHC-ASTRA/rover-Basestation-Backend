from util.websocket_types import WebsocketData
import random


def generate_random_data(
    data: WebsocketData,
) -> WebsocketData:
    rand_bool = lambda: random.choice([True, False])
    rand_float = lambda: random.uniform(-1, 1)
    rand_int = lambda: random.randint(-10, 10)

    for entry in data.spec:
        if entry.field_type == bool:
            data.data[entry.field] = rand_bool()
        elif entry.field_type == float:
            data.data[entry.field] = rand_float()
        elif entry.field_type == int:
            data.data[entry.field] = rand_int()
        elif issubclass(entry.field_type, WebsocketData):
            data.data[entry.field] = generate_random_data(entry.field)

    return data
