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
            print(data.data[entry.field])
            data.data[entry.field] = generate_random_data(data.data[entry.field])

    return data


def generate_cumulative_data(
    data: WebsocketData,
) -> WebsocketData:
    rand_bool = lambda: random.choice([True, False])
    rand_float = lambda: random.uniform(0, 1)
    rand_int = lambda: random.randint(0, 10)

    for entry in data.spec:
        if entry.field_type == bool:
            data.data[entry.field] = rand_bool()
        elif entry.field_type == float:
            data.data[entry.field] += (
                1200 * data.data[entry.field] + rand_float()
            ) / 100
        elif entry.field_type == int:
            data.data[entry.field] += int(rand_int() / 10)
        elif issubclass(entry.field_type, WebsocketData):
            print(data.data[entry.field])
            data.data[entry.field] = generate_cumulative_data(data.data[entry.field])

    return data
