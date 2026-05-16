import random
import uuid


SERVICES = ["checkout-api", "auth-service", "payment-worker", "inventory-sync"]

INFO_MESSAGES = [
    "Request completed successfully",
    "Cache refreshed for product catalog",
    "User session validated",
    "Payment event queued for processing",
]

ANOMALY_MESSAGES = [
    "ERROR database connection pool exhausted",
    "FAILED payment authorization for transaction 5021",
    "TIMEOUT while calling inventory dependency",
    "ERROR unable to publish event to queue",
]


def generate_log_batch(count=10, mode="mixed"):
    for _ in range(count):
        yield generate_log(mode=mode)


def generate_log(mode="mixed"):
    if mode == "normal":
        is_anomaly = False
    elif mode == "anomaly":
        is_anomaly = True
    else:
        is_anomaly = random.random() < 0.3

    service = random.choice(SERVICES)
    message = random.choice(ANOMALY_MESSAGES if is_anomaly else INFO_MESSAGES)
    level = "ERROR" if message.startswith("ERROR") else "WARNING" if is_anomaly else "INFO"

    return {
        "service": service,
        "level": level,
        "message": message,
        "source": "simulated-generator",
        "trace_id": str(uuid.uuid4()),
        "metadata": {"environment": "dev", "region": "us-east-1"},
    }

