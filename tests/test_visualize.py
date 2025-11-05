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
    for i in range(0,50):
        #np.random.seed(42)
        frames = [MockAtoms(np.random.rand(5, 3), np.random.rand(5, 3)) for _ in range(20)]
        new_frames = ResultMD(frames)
        new_frames.name = f"Sim {i}"
        res.append(new_frames)

    return res


"""
def test_plot_scatter(mock_results):
    #res1 = resultMD.ResultMD.from_file("test.traj")
    #res2 = resultMD.ResultMD.from_file("cu.traj")

    vis1 = VisualizeResult(mock_results)

    #vis1.plot_MSD()
    #vis1.plot_scatter("self_diff","lindemann","avg_a",size = 40)
    vis1.plot_histogram("self_diff",200)
"""

def test_invalid_prop_plot_scatter(mock_results):
    """Try plotting a scatter with invalid properties
    """
    vis = VisualizeResult(mock_results)

    with pytest.raises(RuntimeError):
        vis.plot_scatter("self_diff","self_diff","avg_dummy")
    with pytest.raises(TypeError):
        vis.plot_scatter()
    with pytest.raises(RuntimeError):
        vis.plot_scatter("self_diff","avg_dummy","avg_something")

def test_invalid_prop_plot_scatter(mock_results):
    """Try plotting a histogram with invalid properties
    """
    vis = VisualizeResult(mock_results)

    with pytest.raises(RuntimeError):
        vis.plot_histogram("avg_dummy")