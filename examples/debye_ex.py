"""
This script tests the calculation of the debye temperature of
 copper and nickel at different temperatures.
"""

from mdse.md.resultMD import ResultMD
from mdse.rm.runmanager import RunManager
from mdse.parser.parse_yml import main_read
from pathlib import Path

config = main_read("debye.yaml")

rm = RunManager(config)

if not Path("Cu_345.traj").exists():
    rm.run_nve_simulations()

Cu_345 = ResultMD.from_file("Cu_345.traj")
Cu_300 = ResultMD.from_file("Cu_300.traj")
Cu_200 = ResultMD.from_file("Cu_200.traj")
print("Cu 345 K")
print(Cu_345.calc_debye_temperature(frame_skip=0.4))
print("Cu 300 K")
print(Cu_300.calc_debye_temperature(frame_skip=0.4))
print("Cu 200 K")
print(Cu_200.calc_debye_temperature(frame_skip=0.4))
Cu_345.plot_density_of_states()
Cu_300.plot_density_of_states()
Cu_200.plot_density_of_states()
