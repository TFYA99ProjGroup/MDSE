# Copyright (c) 2025 See AUTHORS
#
# This work is licensed under the terms of the MIT license.
# For a copy, see <https://opensource.org/licenses/MIT>.
#
# SPDX-License-Identifier: MIT

from mdse.utils import transfer_chemical_potential, transfer_defect_formation_energy

from mdse.logging.logging_config import setup_logging

setup_logging()

sqlite_path = "../defects.sqlite"

mongodb = "mongodb://admin:secret@localhost:27017/"

transfer_defect_formation_energy(sqlite_path, mongodb_adress=mongodb)
transfer_chemical_potential(sqlite_path, mongodb_adress=mongodb)
