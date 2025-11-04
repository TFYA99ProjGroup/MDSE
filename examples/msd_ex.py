"""
This example utilises the resultMD class to calculate the mean square
displacement of a simulation.
"""

from mdse.md.resultMD import ResultMD
from mdse.rm.runmanager import RunManager
from mdse.parser.parse_yml import main_read
from pathlib import Path

config = main_read("msd.yaml")

rm = RunManager(config)

if not Path("Cu_300.traj").exists():
    rm.run_nve_simulations()

result = ResultMD.from_file("Cu_300.traj")
print(result.calc_msd())
result.visualize_msd()