# Copyright (c) 2025 See AUTHORS
#
# This work is licensed under the terms of the MIT license.
# For a copy, see <https://github.com/TFYA99ProjGroup/MDSE/blob/main/LICENSE>.


"""This module handles reading simulation data for visualization.

It supports reading data from different sources, such as JSON files or a
MongoDB database, based on the provided configuration.
"""


import json
from pathlib import Path
import logging
from pymongo import MongoClient

logger = logging.getLogger(__name__)


def read_data(config_data):
    """Reads simulation data from a specified source (.json or mongoDB).

    This function dispatches to the correct data reading method based on the
    'data_source' key in the configuration dictionary.

    Args:
        config_data (dict): Configuration specifying the data source, location,
            and other necessary parameters.

    Returns:
        list[dict]: A list of dictionaries, where each dictionary contains
            the data for a single simulation.

    Raises:
        RuntimeError: If the configuration is invalid, the specified file is
            not found, or the data cannot be parsed.
        NotImplementedError: If the 'mongo' data source is selected.
    """
    logger.debug("Start getting data to visualize on")
    source = config_data.get("data_source")

    if (source == "json"):
        logger.debug("Found data as .json")
        path = config_data.get("path")
        if not path:
            raise RuntimeError(".json path missing")

        file_path = Path(path)
        logger.debug(f".json found at {file_path}")

        if not file_path.is_file():
            raise RuntimeError("Path not to .json file")

        try:
            with open(file_path,"r") as file:
                data = json.load(file)
        except json.JSONDecodeError:
            raise RuntimeError("Invalid form in .json file")

        logger.debug(f"Succesfully read .json at {file_path}")
        return data


    elif (source == "mongo"):

        uri = config_data.get("uri")
        db_name = config_data.get("database")
        table_name = config_data.get("table")

        if not uri or not db_name or not table_name:
            raise RuntimeError("Config for mongo lacks uri or database or table field")

        client = MongoClient(uri)
        db = client[db_name]
        table = db[table_name]

        #Needs to return [ {sim_id : 1, energy : 2},  {sim_id : 2, energy : 4}] so
        #list of dictionaries.
        #Each dictionary is information about one result/simulation.
        dum = False
        if dum:
            return table

        raise NotImplementedError("Reading from mongoDB is not implemented yet")
