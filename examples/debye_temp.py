from mdse.md.resultMD import ResultMD

result = ResultMD.from_file("Cu_300.traj")
print(result.calc_debye_temperature())
