from mdse.md.resultMD import ResultMD

result = ResultMD.from_file("Cu.traj")
print(result.calc_msd())
result.visualize_msd()
