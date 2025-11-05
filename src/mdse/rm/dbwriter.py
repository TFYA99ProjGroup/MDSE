import glob
import json
import logging
from pymongo import MongoClient

logger = logging.getLogger(__name__)


class DBWriter:
    def __init__(self, resultpath):
        self.client = MongoClient("mongodb://admin:secret@localhost:27017/")
        self.path = resultpath

    def write_jsonfiles_to_db(self):
        db = self.client["materials_db"]
        examples = db["resultexamples"]
        logger.debug(self.path)
        json_files = glob.glob(f"{self.path}/*.json")
        logger.debug(json_files)
        all_docs = []
        for path in json_files:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
                # Om filen innehåller en lista av objekt
                if isinstance(data, list):
                    all_docs.extend(data)
                else:
                    all_docs.append(data)
        if all_docs:
            result = examples.insert_many(all_docs)
            logger.info(f"{len(result.inserted_ids)} document inserted.")
        else:
            logger.info("No documents to insert")
