from ase import Atoms
from ase.md.verlet import VelocityVerlet
from asap3 import Trajectory
from ase.build import bulk
from ase.visualize import view
from asap3 import EMT
from ase import units
from ase.md.velocitydistribution import MaxwellBoltzmannDistribution


class SimulateMD:
    """
    A utility class for setting up and running simple molecular dynamics (MD)
    simulations with ASE (Atomic Simulation Environment).

    This class allows you to construct atoms, molecules, or crystals from a
    given chemical notation and lattice structure, initialize them with a
    velocity distribution, and run MD simulations in the NVE ensemble.

    Example:
    ```sim_list = main_read("examples/test_file.yaml")
    # sim_list[0] is the first simulation
    # sim equals the dictionary of the first simulation
    sim_item = next(iter(sim_list[0].values()))
    # sim_item.get() picks the values from the simulation
    sim = SimulateMD(chem_notation=sim_item['Type'], structure=sim_item.get(
        'Structure'), a=sim_item.get('Lattice'), cubic=sim_item.get('Cubic'),
        temperature=sim_item.get('Temp'),
        timestep=sim_item.get('Timestep'), length=sim_item.get('Length'),
        traj_interval=sim_item.get('TrajInterval'))
    sim.simulate_nve()
    ```

    Parameters
    ----------
    chem_notation : str, optional
        Chemical symbol or formula of the system to simulate (default: 'H').
    structure : str, optional
        Crystal structure type (e.g., 'sc', 'fcc', 'bcc'), used if no explicit
        positions are provided (default: 'sc').
    positions : list or None, optional
        List of explicit atomic positions. If provided, overrides `structure`
        (default: None).
    a : float, optional
        Primary lattice constant (default: 3.6).
    b : float or None, optional
        Secondary lattice constant, only needed for non-cubic cells
        (default: None).
    c : float or None, optional
        Tertiary lattice constant, only needed for non-cubic cells
        (default: None).
    cubic : bool, optional
        Whether to enforce a cubic cell when only `a` is specified
        (default: True).
    temperature : float, optional
        Initial temperature in Kelvin for velocity initialization (default:
        800).
    timestep : float, optional
        Integration timestep in femtoseconds (default: 2).
    length : int, optional
        Total number of integration steps to run (default: 400).
    traj_interval : int, optional
        Interval (in steps) at which to write trajectory snapshots and report
        energy (default: 10).

    Attributes
    ----------
    crystal : ase.Atoms
        The ASE Atoms object representing the constructed system.

    Methods
    -------
    create_crystal() -> Atoms
        Construct an ASE `Atoms` object from the given lattice parameters or
        positions.
    view_super_crystal()
        Visualize a 4x4x4 supercell of the crystal.
    print_energy()
        Print current potential, kinetic, and total energy, as well as
        instantaneous temperature.
    _add_distribution(distribution)
        Apply a velocity distribution (e.g., Maxwell-Boltzmann) to the system at
        the given temperature.
    simulate_nve(calculator=EMT(),
                 distribution=MaxwellBoltzmannDistribution)
        Run a molecular dynamics simulation in the NVE ensemble using Velocity
        Verlet dynamics.
    """

    def __init__(self, config: dict = {}):
        default = {
            "Type": "H",
            "Structure": "sc",
            "Positions": None,
            "Lattice_a": 3.6,
            "Lattice_b": None,
            "Lattice_c": None,
            "Cubic": True,
            "Temp": 800,
            "Timestep": 2,
            "Length": 400,
            "TrajInterval": 10,
        }

        for key, value in default.items():
            if config.get(key) is None:
                config[key] = value

        self.chem_notation = config.get("Type")
        self.structure = config.get("Structure")
        self.positions = config.get("Positions")
        self.a = config.get("Lattice_a")
        self.b = config.get("Lattice_b")
        self.c = config.get("Lattice_c")
        self.cubic = config.get("Cubic")
        self.temperature = config.get("Temp")
        self.timestep = config.get("Timestep") * units.fs
        self.length = config.get("Length")
        self.traj_interval = config.get("TrajInterval")

        self.crystal = self.create_crystal() * (5, 5, 5)

    def create_crystal(self) -> Atoms:
        """Create the atom or molecule or crystal object from the specified params.

        Key args:
        chemNotation -- the chemical notation of the object (default: 'H')
        structure -- The Lattice types or Crystal structure
                     of the object (default: 'sc')
        positions -- Individual atomic positions (optional argument)
        a (float) -- lattice constant
        b (float) -- secondary lattice constant (optional argument)
        c (float) -- third lattice constant (optional argument)
        cubic --
        """
        # Define if we're using structure or positions
        if self.positions is None:
            crystal = bulk(
                self.chem_notation,
                self.structure,
                a=self.a,
                b=self.b,
                c=self.c,
                cubic=self.cubic,
            )
            return crystal

    def view_super_crystal(self):
        """
        Visualize a 4x4x4 supercell of the constructed crystal.

        Notes
        -----
        Requires ASE's `view` function to be available.
        """
        if self.positions is None:
            super_crystal = self.crystal * (4, 4, 4)
            view(super_crystal)
        else:
            raise RuntimeError("Supercell visualization only works with bulk crystals.")

    def print_energy(self):
        """
        Print the current energy and temperature of the system.

        Displays potential energy, kinetic energy, instantaneous temperature,
        and total energy per atom.
        """
        try:
            epot = self.crystal.get_potential_energy()
            ekin = self.crystal.get_kinetic_energy()
            temp = self.crystal.get_temperature()
            print(
                f"Energy per atom: Epot ={epot:6.3f}eV  Ekin = {ekin:.3f}eV "
                f"(T={temp:.3f}K) Etot = {epot + ekin:.3f}eV"
            )
        except Exception as e:
            raise RuntimeError(
                "Energy calculation failed. Ensure calculator is attached."
            ) from e

    def _add_distribution(self, distribution):
        """
        Apply a velocity distribution to initialize atomic velocities.

        Parameters
        ----------
        distribution : callable
            A function that assigns velocities to atoms, e.g.
            `MaxwellBoltzmannDistribution`.
        """
        if not self.temperature:
            raise ValueError("Temperature must be set to apply a distribution.")
        try:
            distribution(self.crystal, temperature_K=self.temperature)
        except Exception as e:
            raise RuntimeError("Failed to apply velocity distribution.") from e

    def simulate_nve(
        self,
        calculator=None,
        distribution=MaxwellBoltzmannDistribution,
        print=False,
    ):
        """
        Run a molecular dynamics simulation in the NVE ensemble using
        Velocity Verlet integration.

        Parameters
        ----------
        calculator : ase.calculators.calculator.Calculator, optional
            The ASE calculator to use for force and energy evaluation
            (default: EMT()).
        distribution : callable, optional
            Function used to initialize velocities (default:
            MaxwellBoltzmannDistribution).

        Notes
        -----
        Trajectory snapshots are written to a `.traj` file with the chemical
        symbols of the system as the filename.
        """
        # TODO: Check w. Petter and Oskar
        # self.crystal = self.crystal*(4, 4, 4)
        try:
            if calculator is None:
                calculator = EMT()

            self._add_distribution(distribution)
            self.crystal.calc = calculator

            dyn = VelocityVerlet(self.crystal, timestep=self.timestep)
            symbols = "".join(set(self.crystal.get_chemical_symbols()))
            traj = Trajectory(f"{symbols}_{self.temperature}.traj", "w", self.crystal)

            dyn.attach(traj.write, interval=self.traj_interval)
            if print:
                dyn.attach(self.print_energy, interval=self.traj_interval)

            dyn.run(self.length)
        except IOError as e:
            raise IOError("Failed to write trajectory file.") from e
        except Exception as e:
            raise RuntimeError("NVE simulation failed.") from e

    def simulate_nvt(self, calculator=EMT(), distribution=MaxwellBoltzmannDistribution):
        try:
            self._add_distribution(distribution)
            self.crystal.calc = calculator

            dyn = Langevin(self.crystal, timestep=self.timestep, temperature_K=self.temperatu    re)# TODO: Friction??!?

        except IOError as e:
            raise IOError("Failed to write trajectory file.") from e
        except Exception as e:
            raise RuntimeError("NVT simulation failed.") from e


    def calculate_specific_heat(self):
        mass = self.crystal.get_masses().sum()
