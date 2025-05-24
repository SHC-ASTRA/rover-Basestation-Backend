from asyncio import run


def test_client():
    from .test_client import main

    run(main())


def test_rover():
    from .test_rover import main

    run(main())


def list_types():
    from .list_types import main

    run(main())
