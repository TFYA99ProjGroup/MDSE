# Copyright (c) 2025 See AUTHORS
#
# This work is licensed under the terms of the MIT license.
# For a copy, see <https://opensource.org/licenses/MIT>.
#
# SPDX-License-Identifier: MIT

"""
Short example script that demonstrates that you can specify a path to a folder in the
config and that the parser will create jobs for each config file in the folder.
"""
from mdse.parser.parse_yml import main_read

simulations = main_read("from_folder.yaml")
# We print the resulting simulations
for sim in simulations:
    print(sim)

print(f"Total number of simulations: {len(simulations)}")
