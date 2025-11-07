from mpi4py import MPI
from mdse.rm.runmanager import RunManager
from mdse.parser.parse_yml import main_read
from mdse.logging.logging_config import setup_logging
import logging
logger = logging.getLogger(__name__)


comm = MPI.COMM_WORLD
rank = comm.Get_rank()
size = comm.Get_size()
setup_logging(debug=False)
simulations_config = main_read("../../../examples/fcc_metals.yaml")

rm = RunManager(simulation_config=simulations_config)

rm.run_simulations()
