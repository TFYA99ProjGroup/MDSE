# Copyright (c) 2025 See AUTHORS
#
# This work is licensed under the terms of the MIT license.
# For a copy, see <https://github.com/TFYA99ProjGroup/MDSE/blob/main/LICENSE>.


"""
Orchestrates the execution of multiple molecular dynamics simulations.

This module provides the `RunManager` class, which is responsible for managing
a list of simulation configurations, distributing them for execution (with MPI
support), and processing the results into a structured, database-friendly format.

Key functionalities include:
- Reading simulation configurations, including expanding configurations based on
  defect structures from an HTTK database.
- Distributing simulation jobs across multiple processes using an MPI-based
  work queue.
- Executing simulations via the `SimulationManager`.
- Post-processing simulation results (`ResultMD` objects) to calculate final
  properties and format them into OPTIMADE-compliant `MongoDBEntry` objects.
- Aggregating results and writing them to a summary JSON file.
"""
from mdse.md.simulationmanager import SimulationManager
import logging
from mpi4py import MPI as _TrueMPI
import uuid
import math
from mdse.rm.dbmanager import MongoDBEntry, DBManager
from datetime import datetime
from mdse.md.resultMD import ResultMD
from pathlib import Path
from httk4mdse.httk_reader import get_defects, save_defects, setup_db
from mdse.parser import get_files

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
        self.MongoDBentriesAsJson = []  # List to store MongoDBEntry instances

        if self.simulation_config is not None:
            self._read_from_sqlite()
            for config in self.simulation_config:
                item = list(config.values())[0]
                logger.debug(f"Adding {item} as a simulation.")
                self.md_simulations.append(SimulationManager(item))

        logger.debug("RunManager done innit bruv!")

    def _read_from_sqlite(self):
        """
        Expands simulation configurations by reading defect structures from a database.

        This method checks if any simulation configuration specifies `DATABASE` as
        the crystal source. If so, it connects to the specified database (via HTTK),
        queries for defect structures, saves them as local files, and then expands
        the simulation list to include a separate simulation for each defect structure.

        Notes
        -----
        This function modifies `self.simulation_config` in place.
        """
        elements_to_remove = []
        for i, item in enumerate(self.simulation_config):
            config = list(item.values())[0]
            crystal_config = config.get("CRYSTAL")
            if crystal_config and crystal_config.get("TYPE") == "DATABASE":
                database_path = crystal_config.get("Filepath")
                logger.debug(f"Load from database at {database_path}")
                self.database = setup_db(database_path)

                query = crystal_config.get("Query", {})

                defect_folder = Path(crystal_config.get("Structure_folder"))
                defects = get_defects(self.database, **query)
                save_defects(defects, defect_folder)

                new_config = {
                    "TYPE": "FILE",
                    "Filepath": str(defect_folder),
                    "Name": crystal_config["Name"],
                }

                config["CRYSTAL"] = new_config

                elements_to_remove.append(i)

                new_sims = get_files([item], str(defect_folder))

                for i, item in enumerate(new_sims):
                    config = list(item.values())[0]
                    if query.get("host") is None:
                        config["CRYSTAL"]["Defect"] = {
                            "defect_key": defects[i][0],
                            "defect_stoichiometry": defects[i][1],
                            "defect_configuration": defects[i][2],
                            "host_material": defects[i][3],
                        }

                self.simulation_config.extend(new_sims)

        for i in elements_to_remove:
            self.simulation_config[i] = None

        for i in elements_to_remove:
            self.simulation_config.remove(None)

        logger.debug(f"simulations after database read: {self.simulation_config}")

    def _add_property(self, property, propertie_values, func):
        """
        Helper to calculate and add a property to a dictionary.

        This function calls a provided function `func`, logs the result, handles
        NaN values by converting them to 0.0, and stores the result in the
        `propertie_values` dictionary.

        Parameters
        ----------
        property : str
            The key under which the calculated value will be stored.
        propertie_values : dict
            The dictionary to which the property will be added.
        func : callable
            A no-argument function that returns the value of the property.
        """
        value = func()
        logger.info(f"{property}: {value}")
        if math.isnan(value):
            value = 0.0
        propertie_values[property] = value

    def run_results(self, result: ResultMD, config):
        """
        Process a finished simulation result and format it as a MongoDB entry.

        This method takes a `ResultMD` object from a completed simulation,
        calculates a standard set of final properties (e.g., Lindemann index,
        self-diffusion), and packages the data into an OPTIMADE-compliant
        `MongoDBEntry` object.

        Parameters
        ----------
        result : ResultMD
            The result object from a completed simulation.
        config : dict
            The configuration dictionary for the simulation that was run.

        Returns
        -------
        MongoDBEntry
            An OPTIMADE-compliant data object ready for database insertion.
        """
        logger.debug(f"Results: {result}")
        logger.debug(f"Config: {config}")
        crystal = config[next(iter(config))]["CRYSTAL"]
        simulation = config[next(iter(config))]["SIMULATION"]
        ensamble = config[next(iter(config))]["ENSAMBLE"]

        final_frame = result.frames[-1]

        logger.debug(crystal)

        entry = MongoDBEntry(
            id=str(crystal["Name"])
            + "_"
            + str(ensamble["Temp"])
            + "K"
            + "_"
            + str(uuid.uuid4())[:8],
            last_modified=datetime.now(),
            elements=list(set(final_frame.get_chemical_symbols())),
            nelements=len(list(set(final_frame.get_chemical_symbols()))),
            mdse_fields={
                "lindemann": result.calc_lindemann(),
                "self_diffusion": result.calc_self_diff(),
                "isobaric_specific_heat": \
                    result.calc_isochoric_heat_capacity_per_atom(),
                "debye": result.calc_debye_temperature(),
                "total_energy": final_frame.info["pot_energy"]
                + final_frame.get_kinetic_energy(),
                **crystal.get("Defect", {}),
                "simulation_parameters": {**ensamble, **simulation},
            },
            chemical_formula_reduced=final_frame.get_chemical_formula(mode="reduce"),
            cartesian_site_positions=final_frame.get_positions().tolist(),
            lattice_vectors=final_frame.get_cell().tolist(),
            nsites=len(final_frame.get_positions()),
            species_at_sites=final_frame.get_chemical_symbols(),
        )
        return entry

    def run_simulations(self):
        """
        Execute all managed simulations distributing them across MPI ranks if available.

        This method implements a master/worker pattern to distribute simulation
        jobs.
        - **If MPI size >= 2**: The master (rank 0) sends job indices to worker
          ranks. Workers execute the simulation, process the results using
          `run_results`, and send the `MongoDBEntry` back to the master.
        - **If MPI size < 2**: The master rank executes all simulations
          sequentially in a single process.
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
                    if msg is None:
                        logger.warning(f"[Master] Worker {src} reported no" +
                                        "entry for last job (skipped/failed).")
                    elif type(msg) is MongoDBEntry:
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
                        comm.send(None, dest=0, tag=TAG_DONE)
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
        """Executes all managed simulations in the NVT ensemble.

        This is a convenience wrapper that calls `simulate_nvt` on each
        `SimulationManager` instance.
        """
        for sim in self.md_simulations:
            sim.simulate_nvt()

    def run_nve_simulations(self):
        """Executes all managed simulations in the NVE ensemble.

        This is a convenience wrapper that calls `simulate_nve` on each
        `SimulationManager` instance.
        """
        for sim in self.md_simulations:
            sim.simulate_nve()

    def run_npt_simulations(self):
        """Executes all managed simulations in the NPT ensemble.

        This is a convenience wrapper that calls `simulate_npt` on each
        `SimulationManager` instance.
        """
        for sim in self.md_simulations:
            sim.simulate_npt()
