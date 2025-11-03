import pytest
import numpy as np
from mdse.md.resultMD import ResultMD #Needed for pytest
from mdse.md.visualize import VisualizeResult

class MockAtoms:
    def __init__(self, positions, velocities=None):
        self.positions = positions
        self.velocities = velocities
        self.info = {
            "dt": 5
        }

    def __len__(self):
        return len(self.positions)

    def __array__(self):
        return self.positions[:,0]

    def get_velocities(self):
        return self.velocities
    
@pytest.fixture
def mock_results():
    res = []
    for i in range(0,2):
        #np.random.seed(42)
        frames = [MockAtoms(np.random.rand(5, 3), np.random.rand(5, 3)) for _ in range(20)]
        new_frames = ResultMD(frames)
        new_frames.name = f"Sim {i}"
        res.append(new_frames)

    return res



def test_plot_3d(mock_results):
    #res1 = resultMD.ResultMD.from_file("test.traj")
    #res2 = resultMD.ResultMD.from_file("cu.traj")

    vis1 = VisualizeResult(mock_results)

    vis1.plot_MSD()
    #vis1.plot_3d("self_diff","lindemann","avg_a",size = 40)

