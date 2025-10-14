from .config import settings
from .logger import setup_logger
import time

logger = setup_logger()

def heartbeat():
    logger.info(f"Barron.AI booting in ENV={settings.ENV}")
    while True:
        logger.info("heartbeat: Barron.AI is alive")
        time.sleep(10)

if __name__ == "__main__":
    heartbeat()
