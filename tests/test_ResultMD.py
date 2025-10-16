import pytest
import numpy as np
import matplotlib.pyplot as plt
from mdse.md.resultMD import ResultMD

class MockAtoms:
    def __init__(self, positions):
        self.positions = positions

    def __len__(self):
        return len(self.positions)


@pytest.fixture
def mock_frames():
    """Generate mock ASE-like frames with positions."""
    np.random.seed(42)
    frames = [MockAtoms(np.random.rand(5, 3)) for _ in range(20)]
    return frames

@pytest.fixture
def mock_linear_walk():
    """Generate a mock linear walk, with predictable diffusion coefficient"""

    pos = np.array([
        [ #Frame 1
            [0,0,1],[0,1,0],[1,0,0]
        ]
    ])

    step = np.array([
        [ #How large steps at each frame, for each atom
            [0,0,1],[0,1,0],[1,0,0]
        ]
    ])
    frames = [MockAtoms(pos)]

    for i in range(1,50):
        pos += step
        frames.append(MockAtoms(pos.copy()))

    return frames

@pytest.fixture
def mock_stationary_walk():
    """Generate a mock stationary walk, with predictable diffusion coefficient"""
    pos = np.array([
        [ #Frame 1
            [0,0,1],[0,1,0],[1,0,0]
        ]
    ])

    frames = [MockAtoms(pos) for _ in range(0,50)]

    return frames

@pytest.fixture
def mock_oscillation_walk():
    """Generate a mock oscillating walk, with predictable diffusion coefficient"""

    pos1 = np.array([
        [ #Frame 1
            [0,0,1],[0,1,0],[1,0,0]
        ]
    ])

    pos2 = np.array([
        [ #How large oscillations
            [0,0,1],[0,1,0],[1,0,0]
        ]
    ])
    frames = [MockAtoms(pos1)]

    for i in range(1,25):
        frames.append(MockAtoms(pos2.copy()))
        frames.append(MockAtoms(pos1.copy()))

    return frames

def test_init_stores_frames(mock_frames):
    """Ensure frames are stored correctly in ResultMD."""
    result = ResultMD(mock_frames)
    result.frames_in_fs = 10
    assert result.frames == mock_frames
    assert len(result.frames) == 20


def test_calc_msd_list_returns_expected_shapes(mock_frames):
    """Check that MSD computation returns correct shapes."""
    result = ResultMD(mock_frames)
    result.frames_in_fs = 10
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
    result.frames_in_fs = 10
    value = result.calc_msd()
    assert isinstance(value, float)
    assert value >= 0


def test_visualize_msd_runs(monkeypatch, mock_frames):
    """Ensure visualize_msd executes without error."""
    result = ResultMD(mock_frames)
    result.frames_in_fs = 10

    monkeypatch.setattr(plt, "show", lambda: None)
    called_plots = []

    def fake_plot(*args, **kwargs):
        called_plots.append((args, kwargs))

    monkeypatch.setattr(plt, "plot", fake_plot)

    result.visualize_msd()
    assert len(called_plots) >= 3  # x, y, z curves expected


def test_calc_self_diff_returns(mock_frames):
    """Ensure calculated self diffusion is correcy type"""
    result = ResultMD(mock_frames)
    Diff_coeff = result.calc_self_diff()
    assert isinstance(Diff_coeff, float)

def test_calc_self_diff_linear_walk(mock_linear_walk):
    """Checks that for a linear walk, self diffusion is greater than zero"""
    result = ResultMD(mock_linear_walk)
    result.frames_in_fs = 1

    Diff_coeff = result.calc_self_diff()

    assert(Diff_coeff > 0)

def test_calc_self_diff_stationary_walk(mock_stationary_walk):
    """Checks that for a stationary crystal, self diffusion is zero"""
    result = ResultMD(mock_stationary_walk)
    result.frames_in_fs = 1

    Diff_coeff = result.calc_self_diff()

    assert(Diff_coeff == 0)

def test_calc_self_diff_oscillation_walk(mock_oscillation_walk):
    """Checks that for a oscillatory crystal, self diffusion is zero"""
    result = ResultMD(mock_oscillation_walk)
    result.frames_in_fs = 1

    Diff_coeff = result.calc_self_diff()

    assert(Diff_coeff == 0)
