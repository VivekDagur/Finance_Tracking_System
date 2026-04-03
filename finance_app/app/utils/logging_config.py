import logging


def configure_logging() -> None:
    """
    Basic logging setup.

    Keeping this centralized avoids duplicated configuration and makes it
    easy to swap handlers later (file logs, JSON logs, etc.).
    """
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    )


def get_logger(name: str) -> logging.Logger:
    return logging.getLogger(name)

