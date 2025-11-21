from pathlib import Path
from httk.atomistic.atomisticio import struct_to_cif
from mdse.parser.classes import DefectCell, DefectInfo
import httk.db
import time

import logging

logger = logging.getLogger(__name__)


def setup_db(db_path: str):
    """
    Initialize an HTTK SQLite-backed database and return a search interface.

    Parameters
    ----------
    db_path : str or Path-like
        Path to the SQLite database file.

    Returns
    -------
    search : httk.db.filteredcollection.FCSqlite
        A searcher object that can be used to query the database.
    """
    backend = httk.db.backend.Sqlite(str(db_path))
    store = httk.db.store.SqlStore(backend)

    search = store.searcher()

    return search


def get_defects(search, **query):
    """
    Query a defect structure from the HTTK database.

    Parameters
    ----------
    search : httk.db.search.Searcher
        The searcher used to run database queries.
    query : dict
        Query to filter the output from the database.

    Returns
    -------
    matches : list
        The retrieved matches for the specified query.
        If no matching entry is found returns None.
    """
    start = time.time()
    search_defect_cell = search.variable(DefectCell)
    search_defect_info = search.variable(DefectInfo)

    search.add(search_defect_info.key == search_defect_cell.key)

    if query.get("key") is not None:
        search.add(search_defect_cell.key == query["key"])

    if query.get("priority") is not None:
        search.add(search_defect_cell.priority == query["priority"])

    search.output(search_defect_cell.key, "key")
    search.output(search_defect_info.defect_stoichiometry, "stoichiometry")
    search.output(search_defect_info.configuration, "configuration")
    search.output(search_defect_cell.defect_structure, "structure")
    query_time = time.time() - start

    logger.debug(f"Query took {query_time:.2f} seconds")

    matches = [defecttuple[0] for defecttuple in list(search)]
    if not matches:
        logger.warning(f"No defect structure found for query: {query}")
        return None

    return matches


def save_to_cif(defect, defects_folder):
    """
    Save an HTTK structure object to a cif file.

    The function writes the structure to a cif file.
    HTTK-specific site metadata (Wyckoff symbols and multiplicities)
    are cleared before export to avoid compatibility issues.

    Parameters
    ----------
    defect : list
        Result from database query as a list of values/objects

    Returns
    -------
    defect_path : Path or None
        The corresponding path to the cif file, or None if save failed.
    """
    key = defect[0]
    structure = defect[3]

    structure.rc_sites.wyckoff_symbols = None
    structure.rc_sites.multiplicities = None

    try:
        defect_path = Path(f"{str(defects_folder)}/_{key}.cif")
        struct_to_cif(structure, str(defect_path))

        return defect_path

    except Exception as e:
        logger.error(f"Failed to save structure to cif: {e}")
        return None


def save_defects(defects, defect_folder):
    """
    Save a collection of defect structures as CIF files.

    Each defect in `defects` is written to the directory specified by
    `defect_folder` using `save_to_cif()`. The function attempts to create the
    target folder if it does not exist, logging a warning if folder creation
    fails. It also logs the time taken to perform the conversion.

    Parameters
    ----------
    defects : iterable
        A sequence of defect objects to save. Each element must be compatible
        with `save_to_cif()`.
    defect_folder : str or Path-like
        Path to the directory where CIF files will be stored.

    Returns
    -------
    list of Path
        A list of file paths corresponding to the saved CIF files.

    Notes
    -----
    - Folder creation errors (e.g., directory already exists) are logged but
      do not interrupt execution.
    - The function logs the total conversion time at debug level.
    """
    start = time.time()
    defect_folder = Path(defect_folder)
    try:
        defect_folder.mkdir()
    except Exception as e:
        logger.warning(e)

    defect_paths = []
    for defect in defects:
        defect_paths.append(save_to_cif(defect, defect_folder))

    conversion_time = time.time() - start
    logger.debug(
        (
            f"Converting {len(defects)} structures to cif "
            f"took {conversion_time:.2f} seconds"
        )
    )
    return defect_paths
