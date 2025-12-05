# Copyright (c) 2025 See AUTHORS
#
# This work is licensed under the terms of the MIT license.
# For a copy, see <https://opensource.org/licenses/MIT>.
#
# SPDX-License-Identifier: MIT

from httklib.httk_reader import (
    setup_db,
    get_defect_formation_energy,
    transfer_chemical_potential,
)

from mdse.logging.logging_config import setup_logging

setup_logging()

store = setup_db("../defects.sqlite")

mongodb = "mongodb://admin:secret@localhost:27017/"

get_defect_formation_energy(store, mongodb)
transfer_chemical_potential(store, mongodb)
