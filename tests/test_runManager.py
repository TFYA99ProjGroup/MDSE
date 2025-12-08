# Copyright (c) 2025 See AUTHORS
#
# This work is licensed under the terms of the MIT license.
# For a copy, see <https://github.com/TFYA99ProjGroup/MDSE/blob/main/LICENSE>.


from mdse.rm.runmanager import RunManager


class DummySim:
    def __init__(self) -> None:
        self.called = False

    def simulate_nve(self):
        self.called = True

    def simulate_nvt(self):
        self.called = True

    def simulate_npt(self):
        self.called = True


def test_run_nve_simulations(monkeypatch):
    # monkeypatch should be used to mock behaviour outside of the testet class.
    monkeypatch.setattr(
        "mdse.rm.runmanager.SimulationManager", lambda config: DummySim()
    )

    fake_config = [{"sim1": {}}, {"sim2": {}}]

    rm = RunManager(fake_config)

    assert len(rm.md_simulations) == 2

    rm.run_nve_simulations()

    for sim in rm.md_simulations:
        assert sim.called is True


def test_run__npt_simulations(monkeypatch):
    # monkeypatch should be used to mock behaviour outside of the testet class.
    monkeypatch.setattr(
        "mdse.rm.runmanager.SimulationManager", lambda config: DummySim()
    )

    fake_config = [{"sim1": {}}, {"sim2": {}}]

    rm = RunManager(fake_config)

    assert len(rm.md_simulations) == 2

    rm.run_npt_simulations()

    for sim in rm.md_simulations:
        assert sim.called is True


def test_run__nvt_simulations(monkeypatch):
    # monkeypatch should be used to mock behaviour outside of the testet class.
    monkeypatch.setattr(
        "mdse.rm.runmanager.SimulationManager", lambda config: DummySim()
    )

    fake_config = [{"sim1": {}}, {"sim2": {}}]

    rm = RunManager(fake_config)

    assert len(rm.md_simulations) == 2

    rm.run_nvt_simulations()

    for sim in rm.md_simulations:
        assert sim.called is True


def test_init_without_config():
    rm = RunManager()

    assert rm.md_simulations == []
