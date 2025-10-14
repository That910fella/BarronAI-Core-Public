from loguru import logger
import time, os

def heartbeat():
    logger.info("Barron.AI service booting...")
    logger.info(f"ENV={os.getenv('ENV', 'dev')}")
    while True:
        logger.info("heartbeat: Barron.AI is alive")
        time.sleep(10)

if __name__ == "__main__":
    try:
        heartbeat()
    except KeyboardInterrupt:
        logger.info("Shutting down cleanly.")
