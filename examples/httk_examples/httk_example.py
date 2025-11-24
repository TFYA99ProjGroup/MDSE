"""
This example showcases how to load a crystal structure from an sqlite
    database into a CIF file.
    Gets the crystal for the NV center in diamond.
"""

from mdse.parser.httk_reader import get_defects, save_to_cif, setup_db

# This example needs a path to a sqlite database
search = setup_db("../../../defects.sqlite")

defect_structures = get_defects(search, key=-4871140043124584231)

defect_folder = save_to_cif(defect_structures[0], ".")

