from mdse.rm.runmanager import RunManager


class DummySim:
    def __init__(self) -> None:
        self.called = False

    def simulate_nve(self):
        self.called = True


def test_run_simulations(monkeypatch):
    # monkeypatch should be used to mock behaviour outside of the testet class.
    monkeypatch.setattr(
        "mdse.rm.runmanager.SimulationManager", lambda config: DummySim()
    )

    fake_config = [{"sim1": {}}, {"sim2": {}}]

    rm = RunManager(fake_config)

    assert len(rm.md_simulations) == 2

    rm.run_simulations()

    for sim in rm.md_simulations:
        assert sim.called is True


def test_init_without_config():
    rm = RunManager()

    assert rm.md_simulations == []
