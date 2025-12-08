# Copyright (c) 2025 See AUTHORS
#
# This work is licensed under the terms of the MIT license.
# For a copy, see <https://github.com/TFYA99ProjGroup/MDSE/blob/main/LICENSE>.


from mdse.rm.runmanager import RunManager
from mdse.parser.parse_yml import main_read
from mdse.logging.logging_config import setup_logging
import logging

logger = logging.getLogger(__name__)
setup_logging(debug=True)

simulations_config = main_read("../fcc_metals.yaml")
rm = RunManager(simulation_config=simulations_config)

rm.run_simulations()
