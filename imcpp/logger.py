import logging

logger = logging.getLogger()
handler = logging.StreamHandler()
formatter = logging.Formatter(
    "%(asctime)s %(levelname)-8s %(message)s", datefmt="%m/%d/%Y %I:%M:%S%p"
)
handler.setFormatter(formatter)
logger.addHandler(handler)
logger.setLevel(logging.INFO)
