from typing import *
from util.websocket_types import WebsocketData
import random


def generate_random_data(
    data: WebsocketData,
) -> WebsocketData:
    rand_bool = lambda: random.choice([True, False])
    rand_float = lambda: random.uniform(-1, 1)
    rand_int = lambda: random.randint(-10, 10)
    rand_string = lambda: "".join(
        [random.choice("abcdefghijklmnopqrstuvwxyz") for _ in range(6)]
    )

    for entry in data.spec:
        if entry.field_type == bool:
            data.data[entry.field] = rand_bool()
        elif entry.field_type == float:
            data.data[entry.field] = rand_float()
        elif entry.field_type == int:
            data.data[entry.field] = rand_int()
        elif entry.field_type == str:
            data.data[entry.field] = rand_string()
        elif issubclass(entry.field_type, WebsocketData):
            print(data.data[entry.field])
            data.data[entry.field] = generate_random_data(data.data[entry.field])

    return data


def generate_cumulative_data(
    data: WebsocketData,
    int_range: Tuple[int, int] = (0, 10),
    float_range: Tuple[float, float] = (0, 1),
) -> WebsocketData:
    rand_bool = lambda: random.choice([True, False])
    rand_float = lambda: random.uniform(*float_range)
    rand_int = lambda: random.randint(*int_range)

    for entry in data.spec:
        if entry.field_type == bool:
            data.data[entry.field] = rand_bool()
        elif entry.field_type == float:
            data.data[entry.field] += rand_float()
        elif entry.field_type == int:
            data.data[entry.field] += rand_int()
        elif issubclass(entry.field_type, WebsocketData):
            print(data.data[entry.field])
            data.data[entry.field] = generate_cumulative_data(data.data[entry.field])

    return data


def generate_random_angle() -> float:
    return random.uniform(-179.9999, 180)


def generate_random_temp() -> float:
    return random.uniform(40, 100)
