from mdse.md.simulationmanager import SimulationManager
import logging
import json
from pathlib import Path
import math

from mpi4py import MPI
logger = logging.getLogger(__name__)


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

    def run_results(self):
        logger.debug(self.result_objects)

        for index, config in enumerate(self.simulation_config):
            logger.debug(config)

            properties = config[next(iter(config))]["RESULT"]["Properties"]

            result = self.result_objects[index]

            logger.debug(properties)
            logger.debug(result)

            propertie_values = {}

            if ("Lindemann" in properties) or ("all" in properties):
                lindemann = result.calc_lindemann()
                logger.info(f"Lindemann: {lindemann}")
                if math.isnan(lindemann):
                    lindemann = 0.0
                propertie_values["Lindemann"] = lindemann

            if ("Self-diffusion" in properties) or ("all" in properties):
                self_diff = result.calc_self_diff()
                if math.isnan(self_diff):
                    self_diff = 0.0
                logger.info(f"Self-diffusion: {self_diff}")
                propertie_values["Self-diffusion"] = self_diff
            # Doesn't work right now
            if ("Isobaric specific heat" in properties) or ("all" in properties):
                ish = result.calc_isochoric_heat_capacity_per_atom()
                if math.isnan(ish):
                    ish = 0.0
                logger.info(f"Isobaric specific heat: {ish}")
                propertie_values["Isobaric specific heat"] = ish

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

            self.docs[index]["Properties"] = propertie_values
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
        if size < 2:
            logger.warning(
                "MPI size < 2. Now the poor Master has to do all the work alone!"
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
