from mdse.md.simulateMD import SimulateMD

class RunManager:
    """Manages settings, io, and execution of simulations.
        
        Args:
            simulation_config (list): list of configurations for each simulation.
    """
    def __init__(self, simulation_config=None) -> None:
        self.md_simulations = []
        self.outputs = []

        if simulation_config is not None:
            for config in simulation_config:
                item = list(config.values())[0]
                self.md_simulations.append(SimulateMD(item))

    def attach_output(self, **kwargs):
        for k, value in kwargs.items():
            if k == "file":
                self.outputs.append(value)

    def write_results(self):
        pass

    def run_simulations(self):
        for sim in self.md_simulations:
            sim.simulate_nve()
