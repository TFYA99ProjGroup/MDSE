from mdse.md.resultMD import ResultMD

result_300 = ResultMD.from_file("Cu_300.traj")
result_200 = ResultMD.from_file("Cu_200.traj")
result_100 = ResultMD.from_file("Cu_100.traj")
print(result_300.calc_debye_temperature(frame_skip=0.4))
result_300.plot_density_of_states()
print(result_200.calc_debye_temperature(frame_skip=0.4))
result_200.plot_density_of_states()
print(result_100.calc_debye_temperature(frame_skip=0.4))
result_100.plot_density_of_states()
