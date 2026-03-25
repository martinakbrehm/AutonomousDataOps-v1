import logging
import sys


def configure_logging():
    fmt = "%(asctime)s %(levelname)s [%(name)s] %(message)s"
    logging.basicConfig(level=logging.INFO, format=fmt, stream=sys.stdout)
    logging.getLogger("uvicorn").setLevel(logging.WARNING)


logger = logging.getLogger("autodops")
