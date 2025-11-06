import pytest
import numpy as np
from mdse.md.resultMD import ResultMD #Needed for pytest
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
    
@pytest.fixture
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

def test_invalid_energy_plot(mock_results):
    """Checks so invalid energy to plot raises error
    """
    vis = VisualizeResult(mock_results)

    with pytest.raises(RuntimeError):
        vis.plot_energy("Dummy_energy")