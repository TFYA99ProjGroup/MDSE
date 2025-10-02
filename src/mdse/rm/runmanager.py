from mdse.md.simulateMD import SimulateMD


class RunManager:
    """Manages settings, I/O, and execution of molecular dynamics simulations.

    This class allows for initializing multiple simulations based on configuration,
    attaching output destinations, executing the simulations, and writing results.

    Args:
        simulation_config (list, optional): A list of dictionaries where each dictionary
            contains configuration parameters for a simulation. Defaults to None.

    Attributes:
        md_simulations (list): A list of SimulateMD instances representing simulations to run.
        outputs (list): A list of output destinations (e.g., file paths) where results can be written.
    """

    def __init__(self, simulation_config=None) -> None:
        """Initializes RunManager with optional simulation configurations.

        If simulation configurations are provided, a SimulateMD instance is created
        for each configuration.

        Args:
            simulation_config (list, optional): A list of dictionaries containing simulation parameters.
        """
        self.md_simulations = []
        self.outputs = []

        if simulation_config is not None:
            for config in simulation_config:
                item = list(config.values())[0]
                self.md_simulations.append(SimulateMD(item))

    def attach_output(self, **kwargs):
        """Attaches output destinations to the RunManager.

        Currently supports attaching file paths for writing results.

        Keyword Args:
            file (str, optional): Path to the file where simulation results should be written.
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

    def run_simulations(self):
        """Executes all simulations managed by this RunManager."""
        for sim in self.md_simulations:
            sim.simulate_nve()
