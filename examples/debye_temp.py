"""
This script tests the calculation of the debye temperature of
 copper and nickel at different temperatures.
"""

from mdse.md.resultMD import ResultMD
from mdse.rm.runmanager import RunManager
from mdse.parser.parse_yml import main_read
from pathlib import Path

config = main_read("fcc_metals.yaml")

rm = RunManager(config)

if not Path("Cu_300.traj").exists():
    rm.run_nve_simulations()

Cu_300 = ResultMD.from_file("Cu_300.traj")
Cu_200 = ResultMD.from_file("Cu_200.traj")
Cu_100 = ResultMD.from_file("Cu_100.traj")
Ni_300 = ResultMD.from_file("Ni_300.traj")
Ni_200 = ResultMD.from_file("Ni_200.traj")
Ni_100 = ResultMD.from_file("Ni_100.traj")

print("Cu 300 K")
print(Cu_300.calc_debye_temperature(frame_skip=0.4))
print("Cu 200 K")
print(Cu_200.calc_debye_temperature(frame_skip=0.4))
print("Cu 100 K")
print(Cu_100.calc_debye_temperature(frame_skip=0.4))
Cu_300.plot_density_of_states()
Cu_200.plot_density_of_states()
Cu_100.plot_density_of_states()

print("Ni 300 K")
print(Ni_300.calc_debye_temperature(frame_skip=0.4))
print("Ni 200 K")
print(Ni_200.calc_debye_temperature(frame_skip=0.4))
print("Ni 100 K")
print(Ni_100.calc_debye_temperature(frame_skip=0.4))
Ni_300.plot_density_of_states()
Ni_200.plot_density_of_states()
Ni_100.plot_density_of_states()
