import glob
import bson
import json
import logging
from pymongo import MongoClient
from pymongo.errors import ServerSelectionTimeoutError
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path

logger = logging.getLogger(__name__)

@dataclass
class MongoDBEntry:
    """
    Minimal dataclass representing a MongoDB structure entry
    complient with the OPTIMADE schema.
    """
    # Must fields
    id: str
    type: str = "structures"
    structure_features: list = field(default_factory=list)

    # In here will be everything custom by us.
    mdse_fields: dict = field(default_factory=dict)

    # Should fields
    last_modified: datetime = None
    elements: list[str] = None
    nelements: int = None
    elements_ratios: list[float] = None
    chemical_formula_descriptive: str = None
    chemical_formula_reduced: str = None
    chemical_formula_anonymous: str = None
    dimension_types: list[int] = None
    nperiodic_dimensions: int = None
    lattice_vectors: list[list[float]] = None
    cartesian_site_positions: list[list[float]] = None
    nsites: int = None
    species_at_sites: list[str] = None
    species: list = None

    # Optional fields
    chemical_formula_hill: str = None
    space_group_symmetry_operations_xyz: list[str] = None
    space_group_symbol_hall: str = None
    space_group_symbol_hermann_mauguin: str = None
    space_group_symbol_hermann_mauguin_extended: str = None
    space_group_it_number: int = None
    assemblies: list[dict] = None

    def to_dict(self) -> dict:
        base = {
            "id": self.id, #must
            # "immutable_id": None, #optional (handled by alias of MongoDB's _id)
            "type": self.type, #must
            "structure_features": self.structure_features, #must, but can be empty list

            # Should fields, very good ideas to have
            "last_modified": self.last_modified,
            "elements": self.elements,
            "nelements": self.nelements,
            "elements_ratios": self.elements_ratios,
            "chemical_formula_descriptive": self.chemical_formula_descriptive,
            "chemical_formula_reduced": self.chemical_formula_reduced,
            "chemical_formula_anonymous": self.chemical_formula_anonymous,
            "dimension_types": self.dimension_types,
            "nperiodic_dimensions": self.nperiodic_dimensions,
            "lattice_vectors": self.lattice_vectors,
            "cartesian_site_positions": self.cartesian_site_positions,
            "nsites": self.nsites,
            "species_at_sites": self.species_at_sites,
            "species": self.species,

            # Optional fields, but good if queryable
            "chemical_formula_hill": self.chemical_formula_hill,
            "space_group_symmetry_operations_xyz":
                self.space_group_symmetry_operations_xyz,
            "space_group_symbol_hall": self.space_group_symbol_hall,
            "space_group_symbol_hermann_mauguin":
                self.space_group_symbol_hermann_mauguin,
            "space_group_symbol_hermann_mauguin_extended":
                self.space_group_symbol_hermann_mauguin_extended,
            "space_group_it_number": self.space_group_it_number,
            "assemblies": self.assemblies,
        }
        base.update(self.mdse_fields)
        return base

    def to_file(self):
        path = Path(f"results/{self.id}.json")
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(self.to_dict(), f, indent=2, default=lambda o: o.isoformat()
                      if hasattr(o, 'isoformat') else o)


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

    @staticmethod
    def create_json_from_mongodbentries(entries: list[MongoDBEntry]):
        path = Path("results/all_results_v2.json")
        path.parent.mkdir(parents=True, exist_ok=True)

        if path.exists():
            with open(path, "r", encoding="utf-8") as f:
                try:
                    existing_docs = json.load(f)
                except json.JSONDecodeError:
                    existing_docs = []
        else:
            existing_docs = []

        all_docs = existing_docs + entries

        with open(path, "w", encoding="utf-8") as f:
            json.dump(all_docs, f, indent=2, default=lambda o: o.isoformat()
                      if hasattr(o, 'isoformat') else o)
        return

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
                    data["last_modified"] = datetime.fromisoformat(
                        data["last_modified"]
                    )
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

    def read_from_db(self, conditions, outputs,collection_str="structures"):
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
        collection_str : str
            String that defines what collection to query, default value perserver
            legacy behavior

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
        collection = db[collection_str]

        docs = collection.find(conditions)
        result = {}
        for doc in docs:
            result[str(doc["_id"])] = {}
            for requested_output in outputs:
                result[str(doc["_id"])][requested_output] = self._get_nested(
                    doc, requested_output
                )

        return result

    def get_all_values(self, field, collection_str="structures"):
        """
        Return a list of all values that appear for a given field in a collection.
        Supports nested fields via dot notation (e.g. 'properties.lindemann').
        """
        db = self.client["materials_db"]
        coll = db[collection_str]

        cursor = coll.find(
            {field: {"$exists": True}},
            {field: 1, "_id": 0}
        )

        values = []
        for doc in cursor:
            # Extract nested value using your existing helper
            val = self._get_nested(doc, field)
            if isinstance(val, list):
                values.extend(val)     # flatten lists
            else:
                values.append(val)

        return values
