from pathlib import Path
from mdse.md.simulationmanager import SimulationManager
import logging
from mpi4py import MPI as _TrueMPI
import math
from mdse.rm.dbmanager import MongoDBEntry, DBManager
from datetime import datetime
import secrets
from mdse.parser.httk_reader import get_defects, save_defects, setup_db
from mdse.parser.parse_yml import get_files
from mdse.md.resultMD import ResultMD

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
        self.docs = []
        self.simulation_config = simulation_config
        self.MongoDBentriesAsJson = [] # List to store MongoDBEntry instances

        if self.simulation_config is not None:
            self._read_from_sqlite()
            for config in self.simulation_config:
                item = list(config.values())[0]
                logger.debug(f"Adding {item} as a simulation.")
                try:
                    self.md_simulations.append(SimulationManager(item))

                except Exception as e:
                    self.md_simulations.append(None)
                    logger.error(
                        f"Failed to add simulation {item} to md_simulations: {e}"
                    )

        logger.debug("RunManager done innit bruv!")

    def _read_from_sqlite(self):
        crystal_config = list(self.simulation_config[0].values())[0].get("CRYSTAL")
        if crystal_config and crystal_config.get("TYPE") == "DATABASE":
            database_path = crystal_config.get("Filepath")
            logger.debug(f"Load from database at {database_path}")
            self.database = setup_db(database_path)

            query = crystal_config.get("Query")

            defect_folder = Path("./defects")
            defects = get_defects(self.database, **query)
            save_defects(defects, defect_folder)

            for config in self.simulation_config:
                item = list(config.values())[0]

                crystal_config = {
                    "TYPE": "FILE",
                    "Filepath": str(defect_folder),
                }

                item["CRYSTAL"] = crystal_config

            self.simulation_config = get_files(
                self.simulation_config, str(defect_folder)
            )
            for i, config in enumerate(self.simulation_config):
                item = list(config.values())[0]
                item["CRYSTAL"]["Defect"] = {
                    "key": defects[i][0],
                    "stoichiometry": defects[i][1],
                    "configuration": defects[i][2],
                }
            logger.debug(f"simulations after database read: {self.simulation_config}")

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

    def run_results(self, result: ResultMD, config):
        logger.debug(f"Results: {result}")
        crystal = config[next(iter(config))]["CRYSTAL"]
        simulation = config[next(iter(config))]["SIMULATION"]
        ensamble = config[next(iter(config))]["ENSAMBLE"]

        final_frame = result.frames[-1]

        entry = MongoDBEntry(
            id=str(crystal["Name"]) + "_" + str(ensamble["Temp"]) + "K",
            last_modified=datetime.now(),
            elements=list(set(final_frame.get_chemical_symbols())),
            nelements=len(list(set(final_frame.get_chemical_symbols()))),
            mdse_fields={
                "lindemann": result.calc_lindemann(),
                "self_diffusion": result.calc_self_diff(),
                "isobaric_specific_heat":
                    result.calc_isochoric_heat_capacity_per_atom(),
                "debye": result.calc_debye_temperature(),
                "total_energy": final_frame.info["pot_energy"]
                    + final_frame.get_kinetic_energy(),
                "defect": crystal.get("Defect", None),
                "simulation_parameters": {**ensamble, **simulation},
            },
            chemical_formula_reduced=final_frame.get_chemical_formula(mode="reduce"),
            cartesian_site_positions=final_frame.get_positions().tolist(),
            lattice_vectors=final_frame.get_cell().tolist(),
            nsites=len(final_frame.get_positions()),
            species_at_sites=final_frame.get_chemical_symbols(),
        )
        return entry

    def run_simulations(self, overwrite_ensamble=None):
        """
        Distribute simulations across MPI ranks using a work queue.
        Each rank (not including master) runs simulations.
        """
        comm = MPI.COMM_WORLD
        rank = comm.Get_rank()
        size = comm.Get_size()
        if size < 2:
            logger.warning(
                "MPI size < 2. Now the poor Master has to do all the work alone!"
            )
            for index, sim in enumerate(self.md_simulations):
                if sim is None:
                    logger.error("Simulation is None, skipping")
                    continue
                if overwrite_ensamble is not None:
                    sim.ensamble = overwrite_ensamble
                res = sim.simulate()
                config = self.simulation_config[index]
                entry = self.run_results(res, config)
                self.MongoDBentriesAsJson.append(entry.to_dict())
            DBManager.create_json_from_mongodbentries(self.MongoDBentriesAsJson)
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
                msg = comm.recv(source=MPI.ANY_SOURCE, tag=MPI.ANY_TAG, status=status)
                src = status.Get_source()
                tag = status.Get_tag()
                logger.debug(f"[Master] Received {msg} from worker {src}")

                if tag == TAG_DONE:
                    if type(msg) is MongoDBEntry:
                        self.MongoDBentriesAsJson.append(msg.to_dict())
                    if jobs:
                        job = jobs.pop(0)
                        logger.debug(f"[Master] Sent new job {job} to worker {src}")
                        comm.send(job, dest=src, tag=TAG_WORK)
                    else:
                        logger.debug(f"[Master] Sent stop signal to worker {src}")
                        comm.send(None, dest=src, tag=TAG_STOP)
                        finished_workers += 1

            logger.debug("[Master] All jobs completed.")
            DBManager.create_json_from_mongodbentries(self.MongoDBentriesAsJson)
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
                    if sim is None:
                        logger.error("Simulation is None, skipping")
                        continue
                    res = sim.simulate()
                    #############################################
                    config = self.simulation_config[job]
                    logger.debug(f"config::: {config}")
                    database_entry = self.run_results(res, config)
                    logger.debug(f"[Worker {rank}] Completed job {job}")
                    comm.send(database_entry, dest=0, tag=TAG_DONE)
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
