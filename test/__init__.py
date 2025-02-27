import asyncio


def launch(func):
    asyncio.run(func())


def test_client():
    from .test_client import main

    launch(main)


def test_rover():
    from .test_rover import main

    launch(main)


def list_types():
    from .list_types import main

    launch(main)
