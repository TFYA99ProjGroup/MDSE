"""
This example utilises the resultMD class to calculate the mean square
displacement of a simulation.
"""
from mdse.md.resultMD import ResultMD

result = ResultMD.from_file("Cu.traj")
print(result.calc_msd())
result.visualize_msd()
