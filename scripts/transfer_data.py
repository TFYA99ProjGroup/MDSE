from mdse.parser.httk_reader import setup_db, get_defect_formation_energy

store = setup_db("../defects.sqlite")

get_defect_formation_energy(store)
