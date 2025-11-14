import glob
import bson
import json
import logging
from pymongo import MongoClient
from pymongo.errors import ServerSelectionTimeoutError

logger = logging.getLogger(__name__)


class DBWriter:
    """
    Handles writing JSON result files to a MongoDB database.

    This class establishes a MongoDB connection, searches a given directory
    for result files (JSON), and uploads their contents into a
    predefined MongoDB collection.

    Attributes
    ----------
    client : MongoClient
        The MongoDB client used to communicate with the database.
    path : str
        Filesystem path to the directory containing result files.
    """

    def __init__(self, resultpath, adress):
        """
        Initialize a DBWriter instance and connect to a MongoDB server.

        Parameters
        ----------
        resultpath : str
            Path to the directory containing result files (JSON).
        adress : str
            MongoDB connection string or address (e.g. "mongodb://localhost:27017/").

        Notes
        -----
        - Attempts to ping the MongoDB server to verify connectivity.
        - Logs an error if the server is unreachable.
        """
        # self.client = MongoClient("mongodb://admin:secret@localhost:27017/")
        self.client = MongoClient(
            adress,
            serverSelectionTimeoutMS=2000,
            connectTimeoutMS=2000,
            socketTimeoutMS=2000,
        )
        try:
            self.client.admin.command("ping")
        except ServerSelectionTimeoutError as e:
            logger.error(f"MongoClient is not connected: {e}")

        self.path = resultpath

    def write_jsonfiles_to_db(self, db_str="materials_db", collection_str="structures"):
        """
        Upload all JSON files from `self.path` to the MongoDB collection
        `structures`.

        The method:
        1. Scans the directory specified by `self.path` for `.json` files.
        2. Reads each file into a Python dictionary.
        3. Inserts all documents into the MongoDB collection.

        Logs
        ----
        - Debug: Lists found files and their contents before insertion.
        - Info: Number of successfully inserted documents.
        """
        db = self.client[db_str]
        examples = db[collection_str]
        logger.debug(self.path)
        json_files = glob.glob(f"{self.path}/*.json")
        logger.debug(json_files)
        all_docs = []
        for path in json_files:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
                all_docs.append(data)
        logger.debug(all_docs)
        if all_docs:
            result = examples.insert_many(all_docs)
            logger.info(f"{len(result.inserted_ids)} document inserted.")
        else:
            logger.info("No documents to insert")

    def _write_jsonfiles_to_db_bson(self):
        """Bson variant, not in use right now."""
        db = self.client["materials_db"]
        examples = db["structures"]
        logger.debug(self.path)
        bson_files = glob.glob(f"{self.path}/*.bson")
        logger.debug(bson_files)
        all_docs = []
        for path in bson_files:
            with open(path, "rb") as f:
                data = bson.decode_all(f.read())
                all_docs.extend(data)
        if all_docs:
            result = examples.insert_many(all_docs)
            logger.info(f"{len(result.inserted_ids)} document inserted.")
        else:
            logger.info("No documents to insert")
