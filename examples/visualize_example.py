from mdse.md.resultMD import ResultMD
from mdse.md.visualize import VisualizeResult
from mdse.rm.runmanager import RunManager
from mdse.parser.parse_yml import main_read

def main():

    config = main_read("fcc_metals_short.yaml")
    rm = RunManager(config)

    rm.run_nve_simulations()
    Cu_300 = ResultMD.from_file("Cu_300.traj")
    Cu_300.name = "Cu_300"
    Cu_200 = ResultMD.from_file("Cu_200.traj")
    Cu_200.name = "Cu_200"
    Cu_100 = ResultMD.from_file("Cu_100.traj")
    Cu_100.name = "Cu_100"
    Ni_300 = ResultMD.from_file("Ni_300.traj")
    Ni_300.name = "Ni_300"
    Ni_200 = ResultMD.from_file("Ni_200.traj")
    Ni_200.name = "Ni_200"
    Ni_100 = ResultMD.from_file("Ni_100.traj")
    Ni_100.name = "Ni_100"

    vis = VisualizeResult([Cu_100,Cu_200,Cu_300,Ni_300,Ni_200,Ni_100])

    vis.plot_energy("tot")
    vis.plot_DOS()
    vis.plot_energy("kin")
    vis.plot_MSD()
    vis.plot_scatter("lindemann","self_diff","avg_a")


if __name__ == "__main__":
    main()
