from mdse.md.simulationmanager import SimulationManager
import logging
from mpi4py import MPI as _TrueMPI
logger = logging.getLogger(__name__)

_FORCE_NO_MPI = False # Set to True to simulate missing MPI backend for testing
try:
    comm = _TrueMPI.COMM_WORLD
    _ = comm.Get_rank()
    MPI = _TrueMPI
    _MPI_AVAILABLE = True
    if _FORCE_NO_MPI:
        raise RuntimeError("Simulated missing MPI backend")
except Exception as e:
    logger.warning(
        f"No working MPI backend detected ({e}). Falling back to single-process mode."
        )
    _MPI_AVAILABLE = False
    # This below is not strictly necessary since we never use 'comm'
    # in single-process mode, but it's here for completeness.
    class _FakeComm:
        def Get_rank(self): return 0
        def Get_size(self): return 1
        def send(self, *_, **__): pass
        def recv(self, *_, **__): return None

    class _FakeMPI:
        COMM_WORLD = _FakeComm()
        ANY_SOURCE = 0
        ANY_TAG = 0
        Status = object

    MPI = _FakeMPI()

class RunManager:
    """Manages settings, I/O, and execution of molecular dynamics simulations.

    This class allows for initializing multiple simulations based on configuration,
    attaching output destinations, executing the simulations, and writing results.

    Args:
        simulation_config (list, optional): A list of dictionaries where each dictionary
            contains configuration parameters for a simulation. Defaults to None.

    Attributes:
        md_simulations (list): A list of SimulationManager instances representing
                            simulations to run.
        outputs (list): A list of output destinations (e.g., file paths) where results
                        can be written.
    """

    def __init__(self, simulation_config=None) -> None:
        """Initializes RunManager with optional simulation configurations.

        If simulation configurations are provided, a SimulationManager instance is
        created for each configuration.

        Args:
            simulation_config (list, optional): A list of dictionaries containing
                                                simulation parameters.
        """
        logger.debug(
            f"Initializes an instance of RunManager with config {simulation_config}")

        self.md_simulations = []
        self.outputs = []

        if simulation_config is not None:
            for config in simulation_config:
                item = list(config.values())[0]
                logger.debug(f"Adding {item} as a simulation.")
                self.md_simulations.append(SimulationManager(item))

        logger.debug("RunManager done innit bruv!")

    def attach_output(self, **kwargs):
        """Attaches output destinations to the RunManager.

        Currently supports attaching file paths for writing results.

        Keyword Args:
            file (str, optional): Path to the file where simulation results should be
                                    written.
        """
        for k, value in kwargs.items():
            if k == "file":
                self.outputs.append(value)

    def write_results(self):
        """Writes the results of simulations to the attached output destinations.

        This method is a placeholder and should be implemented to handle writing
        simulation results (e.g., to files or other storage).
        """
        pass

    def run_simulations(self, overwrite_ensamble=None):
        """
        Distribute simulations across MPI ranks using a work queue.
        Each rank (not including master) runs simulations.
        """
        comm = MPI.COMM_WORLD
        rank = comm.Get_rank()
        size = comm.Get_size()
        if (not _MPI_AVAILABLE) or (size < 2):
            logger.info(
                "Running in single-process mode (single rank or no MPI backend)."
                )
            for sim in self.md_simulations:
                if overwrite_ensamble is not None:
                    sim.ensamble = overwrite_ensamble
                sim.simulate()
            # Insert single core execution here if desired
            return

        TAG_WORK = 1
        TAG_DONE = 2
        TAG_STOP = 3

        # Only master prepares the list of jobs
        if rank == 0:
            finished_workers = 0
            num_workers = size - 1
            jobs = list(range(len(self.md_simulations)))

            while finished_workers < num_workers:
                status = MPI.Status()
                _ = comm.recv(source=MPI.ANY_SOURCE, tag=MPI.ANY_TAG, status=status)
                src = status.Get_source()
                tag = status.Get_tag()

                if tag == TAG_DONE:
                    if jobs:
                        job = jobs.pop(0)
                        logger.debug(f"[Master] Sent new job {job} to worker {src}")
                        comm.send(job, dest=src, tag=TAG_WORK)
                    else:
                        logger.debug(f"[Master] Sent stop signal to worker {src}")
                        comm.send(None, dest=src, tag=TAG_STOP)
                        finished_workers += 1

            logger.debug("[Master] All jobs completed.")
        else:
            # Initialize worker by notifying master
            comm.send("", dest=0, tag=TAG_DONE)
            while True:
                status = MPI.Status()
                job = comm.recv(source=0, tag=MPI.ANY_TAG, status=status)
                tag = status.Get_tag()
                if tag == TAG_WORK:
                    logger.debug(f"[Worker {rank}] Received job {job}")
                    ########## Run the simulation here! #########
                    sim = self.md_simulations[job]
                    sim.simulate()
                    #############################################
                    logger.debug(f"[Worker {rank}] Completed job {job}")
                    comm.send("", dest=0, tag=TAG_DONE)
                elif tag == TAG_STOP:
                    logger.debug(f"[Worker {rank}] Received stop signal from master.")
                    break

    def run_nvt_simulations(self):
        """Executes all simulations managed by this RunManager."""
        for sim in self.md_simulations:
            sim.simulate_nvt()

    def run_nve_simulations(self):
        """Executes all simulations managed by this RunManager."""
        for sim in self.md_simulations:
            sim.simulate_nve()

    def run_npt_simulations(self):
        """Executes all simulations managed by this RunManager."""
        for sim in self.md_simulations:
            sim.simulate_npt()
