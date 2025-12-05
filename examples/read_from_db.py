# Copyright (c) 2025 See AUTHORS
#
# This work is licensed under the terms of the MIT license.
# For a copy, see <https://opensource.org/licenses/MIT>.
#
# SPDX-License-Identifier: MIT

from mdse.rm.dbmanager import DBManager

writer = DBManager("mongodb://admin:secret@localhost:27017/")

result = writer.read_from_db(
    conditions={"composition.elements": "Cu"},
    outputs=[
        "Structure_id",
        "atoms.elements",
        "Properties",
        "composition.chemical_formula_reduced",
    ],
)
print(result)
