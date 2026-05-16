import logging
import sys


class CloudLogFormatter(logging.Formatter):
    def format(self, record):
        base = {
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }

        for key in ("log_id", "alert_id", "service", "rule", "alert_count"):
            if hasattr(record, key):
                base[key] = getattr(record, key)

        return " ".join(f"{key}={value}" for key, value in base.items())


def configure_logging(level="INFO"):
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(CloudLogFormatter())

    root = logging.getLogger()
    root.handlers.clear()
    root.addHandler(handler)
    root.setLevel(level)

