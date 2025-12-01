from mdse.parser.httk_reader import (
    setup_db,
    get_defect_formation_energy,
    transfer_chemical_potential,
)

store = setup_db("../defects.sqlite")

mongodb = "mongodb://admin:secret@localhost:27017/"

get_defect_formation_energy(store, mongodb)
transfer_chemical_potential(store, mongodb)
