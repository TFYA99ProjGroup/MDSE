from mdse.md.simulationmanager import SimulationManager
import logging
import json
from pathlib import Path
import math

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
                self.docs.append({})
        logger.debug("RunManager init done")

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
        for index, sim in enumerate(self.md_simulations):
            if overwrite_ensamble is not None:
                sim.ensamble = overwrite_ensamble
            self.result_objects.append(sim.simulate())

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
