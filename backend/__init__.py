__version__ = "0.1.0"
import coloredlogs, logging
import os

coloredlogs.install(level=os.environ.get("LOG_LEVEL", "DEBUG"))
LOG = logging.getLogger(__name__)


def start():
    from backend.app import main

    main()


def test_client():
    from test import test_client
    import asyncio

    asyncio.run(test_client())


def test_rover():
    from test import test_rover
    import asyncio

    asyncio.run(test_rover())
