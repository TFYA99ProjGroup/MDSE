from mdse.rm.runmanager import RunManager
from mdse.parser.parse_yml import main_read
from mdse.logging.logging_config import setup_logging
import logging

logger = logging.getLogger(__name__)
setup_logging(debug=True)

simulations_config = main_read("fcc_metals.yaml")
rm = RunManager(simulation_config=simulations_config)

rm.run_simulations()
