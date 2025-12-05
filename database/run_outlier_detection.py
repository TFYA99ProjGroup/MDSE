import logging
from mdse.rm.dbmanager import DBManager

logger = logging.getLogger(__name__)

def run_detection():
    """
    An example script to connect to the database and run outlier detection.
    """
    # --- Configuration ---
    mongo_uri = "mongodb://admin:secret@localhost:27017/"

    # --- Main script ---
    logger.debug("Connecting to the database")
    try:
        db_manager = DBManager(mongo_uri)
    except Exception as e:
        logger.error(
            f"Failed to connect to MongoDB. "
            f"Ensure it is running. Error: {e}"
            )
        return

    logger.debug("Running outlier detection with default settings")
    outliers = db_manager.detect_outliers()

    if outliers:
        logger.info(f"Found {len(outliers)} outliers.")
        for outlier in outliers:
            logger.info(
                f"Outlier: "
                f"ID: {outlier['id']}, "
                f"Property: {outlier['property']}, "
                f"Value: {outlier['value']}, "
                f"Group mean: {outlier['mean']}, "
                f"Group std_dev: {outlier['std_dev']}"
                )
    else:
        logger.info("No outliers were found with the current settings.")

if __name__ == "__main__":
    # Configure logging to show INFO level messages
    logging.basicConfig(level=logging.INFO,
                        format='%(asctime)s - %(levelname)s - %(message)s')

    run_detection()
