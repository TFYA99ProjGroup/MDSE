import glob
import bson
import json
import logging
from pymongo import MongoClient
from pymongo.errors import ServerSelectionTimeoutError

logger = logging.getLogger(__name__)


class DBWriter:
    def __init__(self, resultpath, adress):
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

    def write_jsonfiles_to_db(self):
        db = self.client["materials_db"]
        examples = db["resultexamples3"]
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
        examples = db["resultexamples2"]
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
