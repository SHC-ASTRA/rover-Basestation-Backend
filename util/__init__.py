import coloredlogs, logging
import os

# LOGS of utils not showing debug. Investigate
coloredlogs.install(level=os.environ.get("LOG_LEVEL", "DEBUG"))
LOG = logging.getLogger(__name__)
