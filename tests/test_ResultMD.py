import pytest
import numpy as np
import matplotlib.pyplot as plt
from mdse.md.resultMD import ResultMD

@pytest.fixture
def mock_frames():
    """Generate mock ASE-like frames with positions."""
    class MockAtoms:
        def __init__(self, positions):
            self.positions = positions
        def __len__(self):
            return len(self.positions)
    
    np.random.seed(42)
    frames = [MockAtoms(np.random.rand(5, 3)) for _ in range(20)]
    return frames

def test_init_stores_frames(mock_frames):
    """Ensure frames are stored correctly in ResultMD."""
    result = ResultMD(mock_frames)
    assert result.frames == mock_frames
    assert len(result.frames) == 20


def test_calc_msd_list_returns_expected_shapes(mock_frames):
    """Check that MSD computation returns correct shapes."""
    result = ResultMD(mock_frames)
    taus_fs, msd_x, msd_y, msd_z = result._calc_msd_list()

    expected_length = len(range(7, len(mock_frames) - 7))
    assert len(taus_fs) == expected_length
    assert len(msd_x) == expected_length
    assert len(msd_y) == expected_length
    assert len(msd_z) == expected_length
    assert taus_fs[1] - taus_fs[0] == 10


def test_calc_msd_returns_float(mock_frames):
    """Ensure calc_msd returns a single float value."""
    result = ResultMD(mock_frames)
    value = result.calc_msd()
    assert isinstance(value, float)
    assert value >= 0

def test_visualize_msd_runs(monkeypatch, mock_frames):
    """Ensure visualize_msd executes without error."""
    result = ResultMD(mock_frames)

    monkeypatch.setattr(plt,"show", lambda: None)
    called_plots = []

    def fake_plot(*args, **kwargs):
        called_plots.append((args, kwargs))
    monkeypatch.setattr(plt, "plot", fake_plot)

    result.visualize_msd()
    assert len(called_plots) >= 3  # x, y, z curves expected
