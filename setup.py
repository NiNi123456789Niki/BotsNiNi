from db import utils
import logging

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
)

logger = logging.getLogger(__name__)

logger.info("Creating table")

utils.create_table()

logger.info("Table created")

logger.info("Changing table...")
utils.alter_table()
logger.info("Table Changed!")

logger.info("Set up is done")
