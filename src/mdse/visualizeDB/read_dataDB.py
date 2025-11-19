import json
from pathlib import Path
import logging

logger = logging.getLogger(__name__)

"""
Should return a dictionary.
Later, adapt so can read from mongoDB.
But still should return a dictionary

"""


def read_data(config_data):
    """Reads the data we whant to plot. Stored in .json or mongoDB.

    arg:
        config_data(str): Information about data, such as location, what type etc.

    returns:
        data(dic): Dictionary containing the data about simulations
    
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
        raise RuntimeError("Not implemented for mongoDB yet")
