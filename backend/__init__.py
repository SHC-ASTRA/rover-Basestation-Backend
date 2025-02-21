__version__ = "0.1.0"
import coloredlogs, logging
import os

coloredlogs.install(level=os.environ.get("LOG_LEVEL", "info"))
LOG = logging.getLogger(__name__)


def start():
    from backend.app import main

    main()
