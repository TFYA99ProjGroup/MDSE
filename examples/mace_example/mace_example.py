# Copyright (c) 2025 See AUTHORS
#
# This work is licensed under the terms of the MIT license.
# For a copy, see <https://opensource.org/licenses/MIT>.
#
# SPDX-License-Identifier: MIT

"""
Short example with running the mace calculator
"""
from mdse.parser.parse_yml import main_read
from mdse.rm.runmanager import RunManager

config = main_read("metal.yaml")

rm = RunManager(config)
for sim in rm.md_simulations:
    sim.simulate()
