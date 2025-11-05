import pytest
import numpy as np
import matplotlib.pyplot as plt
from mdse.md.resultMD import ResultMD


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
def mock_frames():
    """Generate mock ASE-like frames with positions and velocities."""
    np.random.seed(42)
    frames = [MockAtoms(np.random.rand(5, 3), np.random.rand(5, 3), 1, 2) for _ in range(20)]
    return frames

@pytest.fixture
def mock_frames_simple():
    """Generate mock ASE-like frames with positions. Only two frames, known distances"""
    pos1 = np.array([
        [0.0, 0.0, 0.0],
        [1.0, 0.0, 0.0],
        [0.0, 1.0, 0.0],
        [1.0, 1.0, 0.0]
    ])
    pos2 = np.array([
        [0.0, 0.0, 0.0],
        [2.0, 0.0, 0.0],
        [0.0, 2.0, 0.0],
        [2.0, 2.0, 0.0]
    ])
    frame1 = MockAtoms(pos1)
    frame2 = MockAtoms(pos2)
    frames = [frame1, frame2]
    return frames


@pytest.fixture
def mock_linear_walk():
    """Generate a mock linear walk, with predictable diffusion coefficient"""

    pos = np.array([
        [  # Frame 1
            [0, 0, 1], [0, 1, 0], [1, 0, 0]
        ]
    ])

    step = np.array([
        [  # How large steps at each frame, for each atom
            [0, 0, 1], [0, 1, 0], [1, 0, 0]
        ]
    ])
    frames = [MockAtoms(pos)]

    for i in range(1, 50):
        pos += step
        frames.append(MockAtoms(pos.copy()))

    return frames


@pytest.fixture
def mock_stationary_walk():
    """Generate a mock stationary walk, with predictable diffusion coefficient"""
    pos = np.array([
        [  # Frame 1
            [0, 0, 1], [0, 1, 0], [1, 0, 0]
        ]
    ])

    frames = [MockAtoms(pos) for _ in range(0, 50)]

    return frames


@pytest.fixture
def mock_oscillation_walk():
    """Generate a mock oscillating walk, with predictable diffusion coefficient"""

    pos1 = np.array([
        [  # Frame 1
            [0, 0, 1], [0, 1, 0], [1, 0, 0]
        ]
    ])

    pos2 = np.array([
        [  # How large oscillations
            [0, 0, 1], [0, 1, 0], [1, 0, 0]
        ]
    ])
    frames = [MockAtoms(pos1)]

    for i in range(1, 25):
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


def test_estimate_nearest_neighbor_distance(mock_frames_simple):
    """Ensure the avarage nearest neighbour (distance between atoms) is correct."""
    result = ResultMD(mock_frames_simple)
    positions1 = result.frames[0].positions
    positions2 = result.frames[1].positions

    expected_average1 = 1.0
    expected_average2 = 2.0

    obje1 = result.estimate_nearest_neighbor_distance(positions1)
    obje2 = result.estimate_nearest_neighbor_distance(positions2)

    assert np.isclose(obje1, expected_average1)
    assert np.isclose(obje2, expected_average2)


def test_estimate_average_a(mock_frames_simple):
    """Ensure the mean nearest neighbour over all frames is calculated correctly."""
    system = ResultMD(mock_frames_simple)
    positions1 = system.frames[0].positions
    positions2 = system.frames[1].positions
    obje1 = system.estimate_nearest_neighbor_distance(positions1)
    obje2 = system.estimate_nearest_neighbor_distance(positions2)

    correct_mean = (obje1 + obje2) / 2

    result = system.estimate_average_a()
    assert np.isclose(result, correct_mean)


def test_calc_lindemann_with_mock_frames(mock_frames):
    """Ensure the Lindemann melting criterion is calculated correctly."""
    system = ResultMD(mock_frames)

    lindemann = system.calc_lindemann()
    a = system.estimate_average_a()
    expected = np.sqrt(system.calc_msd()) / a
    assert np.isclose(lindemann, expected)

    a = 0.5
    lindemann2 = system.calc_lindemann(a=a)
    expected2 = np.sqrt(system.calc_msd()) / a
    assert np.isclose(lindemann2, expected2)


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

    assert (Diff_coeff > 0)


def test_calc_self_diff_stationary_walk(mock_stationary_walk):
    """Checks that for a stationary crystal, self diffusion is zero"""
    result = ResultMD(mock_stationary_walk)
    result.frames_in_fs = 1

    Diff_coeff = result.calc_self_diff()

    assert (Diff_coeff == 0)


def test_calc_self_diff_oscillation_walk(mock_oscillation_walk):
    """Checks that for a oscillatory crystal, self diffusion is zero"""
    result = ResultMD(mock_oscillation_walk)
    result.frames_in_fs = 1

    Diff_coeff = result.calc_self_diff()

    assert(Diff_coeff == 0)

def test_calc_debye_temperature(mock_frames):
    result = ResultMD(mock_frames)

    theta_D = result.calc_debye_temperature(frame_skip=0.5)

    assert(theta_D != 0)

def test_calc_density_of_states(mock_frames):
    result = ResultMD(mock_frames)

    dos, omega = result.calc_density_of_states(frame_skip=0.5)

    assert(len(dos) > 0)
    assert(len(omega) > 0)
    for i in range(len(dos)):
        assert(dos[i] >= 0)

def test_energies(mock_frames):
    """Check so getters get the correct energies, and correct amount"""
    result = ResultMD(mock_frames)

    pot_energ = result.get_pot_energies()
    kin_energ = result.get_kin_energies()

    assert(len(mock_frames) == len(pot_energ))
    assert(len(mock_frames) == len(kin_energ))
    
    right_pot = [1]*len(mock_frames)
    right_kin = [2]*len(mock_frames)

    assert(pot_energ == right_pot)
    assert(kin_energ == right_kin)

def test_time_axis(mock_frames):
    """Check so get time axis gets list of times"""
    result = ResultMD(mock_frames)
    times = result.get_time_axis()

    assert(len(times) == len(mock_frames))
