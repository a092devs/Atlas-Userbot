import logging

try:
    from config import config
    LOG_LEVEL = config.LOG_LEVEL
except Exception:
    LOG_LEVEL = "INFO"


def _setup_logger():
    logger = logging.getLogger("Atlas")
    logger.setLevel(LOG_LEVEL)

    if logger.handlers:
        return logger

    handler = logging.StreamHandler()
    formatter = logging.Formatter(
        "[%(asctime)s] [%(levelname)s] %(name)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    handler.setFormatter(formatter)

    logger.addHandler(handler)
    logger.propagate = False
    return logger


log = _setup_logger()
