"""
This example showcases how to load a crystal structure from an sqlite
    database into an ASE `Atoms` object.
    Creates a crystal for the NV center in diamond.
"""

from ase import Atoms
from mdse.parser.httk_reader import load_defect_as_ase, setup_db

# This example needs a path to a sqlite database
search = setup_db("../defects.sqlite")

atoms = load_defect_as_ase("-4871140043124584231", search)
assert type(atoms) is Atoms
