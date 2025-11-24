import glob
import bson
import json
import logging
from pymongo import MongoClient
from pymongo.errors import ServerSelectionTimeoutError

logger = logging.getLogger(__name__)


class DBManager:
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

    def __init__(self, adress):
        """
        Initialize a DBManager instance and connect to a MongoDB server.

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

    def write_jsonfiles_to_db(
        self, path, db_str="materials_db", collection_str="structures"
    ):
        """
        Upload all JSON files from `path` to the MongoDB collection
        `structures`.

        The method:
        1. Scans the directory specified by `path` for `.json` files.
        2. Reads each file into a Python dictionary.
        3. Inserts all documents into the MongoDB collection.

        Logs
        ----
        - Debug: Lists found files and their contents before insertion.
        - Info: Number of successfully inserted documents.
        """
        db = self.client[db_str]
        examples = db[collection_str]
        logger.debug(path)
        json_files = glob.glob(f"{path}/*.json")
        logger.debug(json_files)
        all_docs = []
        for path in json_files:
            with open(path, "r", encoding="utf-8") as f:
                for data in json.load(f):
                    all_docs.append(data)
        logger.debug(all_docs)
        if all_docs:
            result = examples.insert_many(all_docs)
            logger.info(f"{len(result.inserted_ids)} document inserted.")
        else:
            logger.info("No documents to insert")

    def write_dict_to_db(
        self, data, db_str="materials_db", collection_str="structures"
    ):
        db = self.client[db_str]
        collection = db[collection_str]
        if data:
            result = collection.insert_many(list(data.values()))
            logger.info(f"{len(result.inserted_ids)} document inserted.")
        else:
            logger.info("No documents to insert")

    def _write_jsonfiles_to_db_bson(self, resultpath):
        """Bson variant, not in use right now."""
        db = self.client["materials_db"]
        examples = db["structures"]
        logger.debug(resultpath)
        bson_files = glob.glob(f"{resultpath}/*.bson")
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

    def _get_nested(self, doc, key):
        """
        Safely retrieve a nested value from a dictionary using dot notation.

        Parameters
        ----------
        doc : dict
            The dictionary (typically a MongoDB document) to search.
        key : str
            A dot-separated path specifying the nested key to retrieve.

        Returns
        -------
        any or None
            The value found at the nested key path, or ``None`` if any part
            of the path does not exist.
        """
        keys = key.split(".")
        val = doc
        for k in keys:
            if isinstance(val, dict) and k in val:
                val = val[k]
            else:
                return None
        return val

    def read_from_db(self, conditions, outputs):
        """
        Query the MongoDB collection and extract selected fields.

        This method performs a MongoDB ``find`` query using the provided
        conditions, then returns only the requested output fields for each
        matching document. Nested fields can be specified using dot notation,
        which is resolved via ``_get_nested``.

        Parameters
        ----------
        conditions : dict
            MongoDB query conditions passed directly to ``collection.find()``.
        outputs : list of str
            List of fields to extract from each document. Supports dotted
            paths for nested fields (e.g. ``"properties.lindemann"``).

        Returns
        -------
        dict
            A dictionary mapping document IDs (as strings) to dictionaries
            containing the requested output fields. Missing fields resolve to
            ``None``.

        Examples
        --------
        >>> read_from_db(
                {"composition.elements": "Cu"},
                outputs=[
                    "structure_id",
                    "atoms.elements",
                    "Properties",
                    "composition.chemical_formula_reduced",
                    ],
        )
        {
            "65fd12...": {'Structure_id': 'Cu_100K',
                          'atoms.elements': ['Cu', 'Cu', 'Cu', 'Cu'],
                          'Properties': {'Lindemann': 0.01658868622028913,
                                        'Self-diffusion': -8.850633492320649e-09,
                                        'Isobaric specific heat': 4.35330392367842e-22,
                                        'Debye': 1199.8107683415553},
                                        'composition.chemical_formula_reduced': 'Cu'
                                        },
            ...
        }
        """
        db = self.client["materials_db"]
        collection = db["structures"]

        docs = collection.find(conditions)
        result = {}
        for doc in docs:
            result[str(doc["_id"])] = {}
            for requested_output in outputs:
                result[str(doc["_id"])][requested_output] = self._get_nested(
                    doc, requested_output
                )

        return result
