import numpy as np
from mdse.md.resultMD import ResultMD
from mdse.md.visualize import VisualizeResult

class MockAtoms:
    def __init__(self, positions, velocities=None, pot = 0, kin = 0):
        self.positions = positions
        self.velocities = velocities
        self.info = {
            "dt": 5
        }
        self.kinetic_energy = kin
        self.potential_energy = pot

    def __len__(self):
        return len(self.positions)

    def __array__(self):
        return self.positions[:,0]

    def get_velocities(self):
        return self.velocities

    def get_potential_energy(self):
        return self.potential_energy

    def get_kinetic_energy(self):
        return self.kinetic_energy

def mock_results():
    res = []
    for i in range(0,10):
        #np.random.seed(42)
        frames = [MockAtoms(np.random.rand(5, 3),
                            np.random.rand(5, 3),
                            np.random.uniform(40,60),
                            np.random.uniform(10,20)) for _ in range(20)]
        new_frames = ResultMD(frames)
        new_frames.name = f"Sim {i}"
        res.append(new_frames)

    return res


def main():
    #vis = VisualizeResult(mock_results())
    res = ResultMD.from_file("cu_dt.traj")
    res2 = ResultMD.from_file("cu_dt_2.traj")
    vis = VisualizeResult([res,res2])
    vis.plot_energy("kin")
    vis.plot_MSD()

    #vis.plot_scatter("self_diff","lindemann","avg_a")


if __name__ == "__main__":
    main()
