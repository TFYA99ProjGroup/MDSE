from io import StringIO
from httk.atomistic.atomisticio import struct_to_cif
import httk.db
import ase.io

import logging

logger = logging.getLogger(__name__)


def setup_db(db: str):
    """
    Initialize an HTTK SQLite-backed database and return a search interface.

    Parameters
    ----------
    db : str or Path-like
        Path to the SQLite database file.

    Returns
    -------
    search : httk.db.filteredcollection.FCSqlite
        A searcher object that can be used to query the database.
    """
    backend = httk.db.backend.Sqlite(str(db))
    store = httk.db.store.SqlStore(backend)

    search = store.searcher()

    return search


def convert_to_atoms(structure):
    """
    Convert an HTTK structure object into an ASE Atoms object.

    The function writes the structure to a temporary buffer, loads it
    using ASE. HTTK-specific site metadata (Wyckoff symbols and multiplicities)
    are cleared before export to avoid compatibility issues.

    Parameters
    ----------
    structure : httk.atomistic.structure.Structure
        The structure object to convert.

    Returns
    -------
    atoms : ase.Atoms or None
        The corresponding ASE Atoms object, or None if conversion failed.
    """
    structure.rc_sites.wyckoff_symbols = None
    structure.rc_sites.multiplicities = None

    try:
        buffer = StringIO()
        struct_to_cif(structure, buffer)
        buffer.seek(0)

        atoms = ase.io.read(buffer, format="cif")

        return atoms

    except Exception as e:
        logger.error(f"Failed to convert structure to ASE: {e}")
        return None


def load_defect_as_ase(key: str, search, dataType):
    """
    Query a defect structure from the HTTK database and convert it to ASE.

    Parameters
    ----------
    key : str
        Unique identifier of the defect entry in the database.
    search : httk.db.search.Searcher
        The searcher used to run database queries.
    dataType : HTTK data type
        The data model class representing the defect structure schema.

    Returns
    -------
    atoms : ase.Atoms or None
        The retrieved defect structure converted into an ASE Atoms object.
        If no matching entry is found or conversion fails, returns None.
    """
    search_defect_cell = search.variable(dataType)
    search.add(search_defect_cell.key == key)

    search.output(search_defect_cell.defect_structure, "structure")

    matches = list(search)
    if not matches:
        logger.warning(f"No defect structure found for key: {key}")
        return None

    for match, _ in matches:
        structure = match[0]

    atoms = convert_to_atoms(structure)
    if atoms is None:
        logger.error(f"Failed to convert defect structure (key={key}) to ASE.")
    return atoms
