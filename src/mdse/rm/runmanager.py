from mdse.md.simulationmanager import SimulationManager
import logging
from mpi4py import MPI as _TrueMPI
import json
from pathlib import Path
import math

logger = logging.getLogger(__name__)

_FORCE_NO_MPI = False  # Set to True to simulate missing MPI backend for testing
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
    # Should probably be removed later.
    class _FakeComm:
        def Get_rank(self):
            return 0

        def Get_size(self):
            return 1

        def send(self, *_, **__):
            pass

        def recv(self, *_, **__):
            return None

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
            f"Initializes an instance of RunManager with config {simulation_config}"
        )

        self.md_simulations = []
        self.result_objects = []
        self.outputs = []
        self.simulation_config = simulation_config
        self.docs = []

        if simulation_config is not None:
            for config in simulation_config:
                item = list(config.values())[0]
                logger.debug(f"Adding {item} as a simulation.")
                self.md_simulations.append(SimulationManager(item))
                self.docs.append({})

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

    def _add_property(self, property, propertie_values, func):
        value = func()
        logger.info(f"{property}: {value}")
        if math.isnan(value):
            value = 0.0
        propertie_values[property] = value

    def run_results(self):
        logger.debug(f"Results: {self.result_objects}")

        for index, config in enumerate(self.simulation_config):
            logger.debug(config)

            properties = config[next(iter(config))]["RESULT"]["Properties"]

            result = self.result_objects[index]

            logger.debug(properties)
            logger.debug(result)

            property_values = {}
            property_functions = {
                "Lindemann": result.calc_lindemann,
                "Self-diffusion": result.calc_self_diff,
                "Isobaric specific heat": result.calc_isochoric_heat_capacity_per_atom,
                "Debye": result.calc_debye_temperature,
            }

            for name, func in property_functions.items():
                if (name in properties) or ("all" in properties):
                    self._add_property(name, property_values, func)

            crystal = config[next(iter(config))]["CRYSTAL"]
            ensamble = config[next(iter(config))]["ENSAMBLE"]
            self.docs[index]["Structure_id"] = (
                str(crystal["Name"]) + "_" + str(ensamble["Temp"]) + "K"
            )

            atoms = {}
            atoms["elements"] = result.frames[0].get_chemical_symbols()
            atoms["positions"] = result.frames[0].get_positions().tolist()
            atoms["lattice_vectors"] = result.frames[0].get_scaled_positions().tolist()
            self.docs[index]["atoms"] = atoms

            composition = {}
            composition["elements"] = list(set(result.frames[0].get_chemical_symbols()))
            formula, _ = result.frames[0].symbols.formula.reduce()
            composition["chemical_formula_reduced"] = str(formula)
            self.docs[index]["composition"] = composition

            self.docs[index]["Properties"] = property_values
        logger.debug(self.docs)
        logger.debug(len(self.docs))
        for index, doc in enumerate(self.docs):
            path = Path(f"results/test_{index}.json")
            path.parent.mkdir(parents=True, exist_ok=True)
            with open(path, "w") as f:
                json.dump(doc, f)

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
                self.result_objects.append(sim.simulate())
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
                    res = sim.simulate()

                    self.result_objects.append()
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
