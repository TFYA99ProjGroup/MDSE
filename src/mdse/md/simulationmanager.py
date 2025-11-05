import ase.io
from ase import Atoms, units
from ase.md.verlet import VelocityVerlet
from asap3 import LennardJones, Trajectory
from ase.build import bulk
from ase.visualize import view
from asap3 import EMT
from ase.md.nose_hoover_chain import IsotropicMTKNPT, NoseHooverChainNVT
from ase.md.velocitydistribution import MaxwellBoltzmannDistribution, Stationary

import logging

from mdse.md.resultMD import ResultMD

logger = logging.getLogger(__name__)


class SimulationManager:
    """
    A utility class for setting up and running simple molecular dynamics (MD)
    simulations with ASE (Atomic Simulation Environment).

    This class allows you to construct atoms, molecules, or crystals from a
    given chemical notation and lattice structure, initialize them with a
    velocity distribution, and run MD simulations in the NVE, NVT or NPT ensemble.

    Parameters
    ----------
    chem_notation : str, optional
        Chemical symbol or formula of the system to simulate (default: 'Cu').
    structure : str, optional
        Crystal structure type (e.g., 'sc', 'fcc', 'bcc'), used if no explicit
        positions are provided (default: 'fcc').
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
    pressure_au : float, optional
        Pressure constant for NPT measured in atomic units. 1 atm = 3.44e-9 au
        (default: 3.85e-2).
    thermo_time : float, optional
        The characteristic time scale for the thermostat in ASE time units. Typically,
        it is set to 100 times of timestep (default: 100 * units.fs).
    baro_time : float, optional
        The characteristic time scale for the barostat in ASE time units. Typically,
        it is set to 1000 times of timestep (default: 1000 * units.fs).
    Supercell: list, optional
        Enables to create a supercrystal. Defaults to 1x1x1, which is [1,1,1].

    Attributes
    ----------
    crystal : ase.Atoms
        The ASE Atoms object representing the constructed system.

    Examples
    --------

    >>> sim_list = main_read("examples/test_file.yaml")

    sim_list[0] is the first simulation
    sim equals the dictionary of the first simulation

    >>> sim_item = next(iter(sim_list[0].values()))

    sim_item.get() picks the values from the simulation

    >>> sim = SimulationManager(chem_notation=sim_item['Type'], structure=sim_item.get(
    ...    'Structure'), a=sim_item.get('Lattice'), cubic=sim_item.get('Cubic'),
    ...    temperature=sim_item.get('Temp'),
    ...    timestep=sim_item.get('Timestep'), length=sim_item.get('Length'),
    ...   traj_interval=sim_item.get('TrajInterval'))
    >>> sim.simulate_nve()
    """

    def __init__(self, config: dict = {}, create_trajectory=False):
        logger.debug(f"Initialize an instance of SimulateMD with config {config}")
        default = {
            "Type": "Cu",
            "Structure": "fcc",
            "Positions": None,
            "Lattice_a": 3.6,
            "Lattice_b": None,
            "Lattice_c": None,
            "Cubic": True,
            "Temp": 800,
            "Timestep": 2,
            "Length": 400,
            "TrajInterval": 10,
            "Pressure": 3.85e-2,
            "ThermoTime": 100 * units.fs,
            "BaroTime": 1000 * units.fs,
            "Supercrystal": [1, 1, 1],
            "Ensamble": "NVE"
        }
        for key, value in default.items():
            if config.get(key) is None:
                config[key] = value

        if config.get("Crystal") is not None:
            try:
                self.crystal = ase.io.read(config.get("Crystal"))
            except Exception as e:
                logger.error(e)
                raise
        else:
            self.crystal = self.create_crystal(
                chem_notation=config.get("Type"),
                structure=config.get("Structure"),
                a=config.get("Lattice_a"),
                b=config.get("Lattice_b"),
                c=config.get("Lattice_c"),
                cubic=config.get("Cubic"),
                positions=config.get("Positions"),
            ) * tuple(config.get("Supercrystal"))

        self.temperature = config.get("Temp")
        self.timestep = config.get("Timestep") * units.fs
        self.length = config.get("Length")
        self.traj_interval = config.get("TrajInterval")
        self.pressure_au = config.get("Pressure")
        self.thermo_time = config.get("ThermoTime")
        self.baro_time = config.get("BaroTime")
        self.create_trajectory = create_trajectory
        self.result = [self.crystal]
        self.positions = config.get("Positions")
        self.ensamble = config.get("Ensamble")

        logger.debug("Init done")

    def create_crystal(
        self, chem_notation, structure, a, b, c, cubic, positions=None
    ) -> Atoms:
        """Create the atom or molecule or crystal object from the specified params.

        Parameters
        ----------
        chem_notation : str
            The chemical notation of the object.
        structure : str
            The Lattice types or Crystal structure of the object.
        a : float
            Lattice constant.
        b : float
            Secondary lattice constant (optional argument).
        c : float
            Third lattice constant (optional argument).
        cubic : bool
            Sets cubic unit cell.
        positions : list
            Individual atomic positions (optional argument).
        """
        logger.debug("Creating crystal")

        # Define if we're using structure or positions
        if positions is None:
            crystal = bulk(
                chem_notation,
                structure,
                a=a,
                b=b,
                c=c,
                cubic=cubic,
            )
            return crystal
        else:
            logger.error("Can not initialize from parameters.")
            raise NotImplementedError()

    def view_super_crystal(self):
        """
        Visualize a supercell of the constructed crystal (3x3x3 as default).

        Notes
        -----
        Requires ASE's `view` function to be available.
        """
        logger.debug("Viewing super crystal")
        if self.positions is None:
            super_crystal = self.crystal
            view(super_crystal)
        else:
            raise RuntimeError(
                "Supercell visualization only works with bulk crystals.")

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
            logger.info(
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
            raise ValueError(
                "Temperature must be set to apply a distribution.")
        try:
            distribution(self.crystal, temperature_K=self.temperature)
            Stationary(self.crystal)
        except Exception as e:
            raise RuntimeError("Failed to apply velocity distribution.") from e

    def _check_calculator(self, calculator, calc_params):
        """
        Validate and initialize an ASE calculator.

        This method checks whether a valid calculator has been specified and returns
        an initialized instance accordingly. If no calculator is provided, the EMT
        (Effective Medium Theory) calculator is used by default.

        Parameters
        ----------
        calculator : str or None
            The calculator to use for energy and force evaluations. Can be:
              - None: defaults to EMT.
              - "EMT": uses the ASE EMT calculator.
              - "LennardJones": uses the ASE Lennard-Jones calculator.
            Any other value raises a NotImplementedError.

        calc_params : dict
            Keyword arguments passed to the chosen calculator's constructor.

        Returns
        -------
        ase.calculators.Calculator
            An initialized ASE calculator instance corresponding to the specified type.

        Raises
        ------
        NotImplementedError
            If the specified calculator type is not supported.

        Notes
        -----
        Supported calculators:
          - ``EMT``
          - ``LennardJones``
        """
        if calculator is None:
            logger.debug("No calculator specified, EMT used as default")
            calculator = EMT(**calc_params)
        elif calculator == "EMT":
            calculator = EMT(**calc_params)
        elif calculator == "LennardJones":
            calculator = LennardJones(**calc_params)
        else:
            error_msg = (
                f"Calculator {calculator} not implemented, "
                "valid calculators are: EMT, LennardJones"
            )
            raise NotImplementedError(error_msg)

        return calculator

    def _attach_outputs(self, dyn, print):
        """Attach outputs to simulation."""
        symbols = "".join(set(self.crystal.get_chemical_symbols()))
        if self.create_trajectory:
            traj = Trajectory(f"{symbols}_{self.temperature}.traj", "w", self.crystal)
            dyn.attach(traj.write, interval=self.traj_interval)

        if print:
            dyn.attach(self.print_energy, interval=self.traj_interval)

        dyn.attach(self.result.append, self.traj_interval, self.crystal.copy())

    def simulate(self,
                 calculator=None,
                 calc_params={},
                 distribution=MaxwellBoltzmannDistribution,
                 print=False,):
        if self.ensamble.lower() == "nve":
            self.simulate_nve(calculator, calc_params, distribution, print)
        elif self.ensamble.lower() == "nvt":
            self.simulate_nvt(calculator, calc_params, distribution, print)
        elif self.ensamble.lower() == "npt":
            self.simulate_npt(calculator, calc_params, distribution, print)
        else:
            msg = f"Not supperted ensamble tried to be used: {self.ensamble} "
            "Please use one of following: NVE, NVT, NPT"
            logger.error(msg)
            raise ValueError(msg)

    def simulate_nve(
        self,
        calculator=None,
        calc_params={},
        distribution=MaxwellBoltzmannDistribution,
        print=False,
    ):
        """
        Run a molecular dynamics simulation in the NVE ensemble using
        ``VelocityVerlet`` integration.

        Parameters
        ----------
        calculator : str, optional
            The ASE calculator to use for force and energy evaluation
            (default: ``'EMT'``).
        calc_params: dictionary, optional
            Parameters to pass on to calculator as a dictionary.
        distribution : callable, optional
            Function used to initialize velocities (default:
            ``MaxwellBoltzmannDistribution``).

        Returns
        -------
        ResultMD
            An object containing the simulation data.

        Notes
        -----
        If ``create_trajectory`` is ``True`` Trajectory snapshots are written to
        a `.traj` file with the chemical symbols of the system as the filename.
        Otherwise the snapshots will be written to a :class:`~ResultMD`
        """

        try:
            symbols = "".join(set(self.crystal.get_chemical_symbols()))
            logger.debug(f"Beggining simulation of {symbols}_{self.temperature}")

            self._add_distribution(distribution)

            self.crystal.info["dt"] = self.timestep
            self.crystal.calc = self._check_calculator(calculator, calc_params)

            dyn = VelocityVerlet(self.crystal, timestep=self.timestep)

            self._attach_outputs(dyn, print)

            dyn.run(self.length)
            logger.debug("Simulation done")
        except IOError as e:
            logger.error(e)
            raise IOError("Failed to write trajectory file.") from e
        except Exception as e:
            logger.error(e)
            raise
        return ResultMD(self.result)

    def simulate_npt(
        self,
        calculator=None,
        calc_params={},
        distribution=MaxwellBoltzmannDistribution,
        print=False,
    ):
        """
        Run a molecular dynamics simulation in the NPT ensemble using
        ``IsotropicMTKNPT`` integration.

        Parameters
        ----------
        calculator : str, optional
            The ASE calculator to use for force and energy evaluation
            (default: ``'EMT'``).
        distribution : callable, optional
            Function used to initialize velocities (default:
            ``MaxwellBoltzmannDistribution``).

        Returns
        -------
        ResultMD
            An object containing the simulation data.

        Notes
        -----
        If ``create_trajectory`` is ``True`` Trajectory snapshots are written to
        a `.traj` file with the chemical symbols of the system as the filename.
        Otherwise the snapshots will be written to a :class:`~ResultMD`
        """

        try:
            self._add_distribution(distribution)
            self.crystal.calc = self._check_calculator(calculator, calc_params)

            self.crystal.info["p_au"] = self.pressure_au
            dyn = IsotropicMTKNPT(
                self.crystal,
                timestep=self.timestep,
                temperature_K=self.temperature,
                pressure_au=self.pressure_au,
                tdamp=self.thermo_time,
                pdamp=self.baro_time,
            )
            self._attach_outputs(dyn, print)

            dyn.run(self.length)
        except IOError as e:
            logger.error(e)
            raise IOError("Failed to write trajectory file.") from e
        except Exception as e:
            logger.error(e)
            raise
        return ResultMD(self.result)

    def simulate_nvt(
        self,
        calculator=None,
        calc_params={},
        distribution=MaxwellBoltzmannDistribution,
        print=False,
    ):
        """
        Run a molecular dynamics simulation in the NVT ensemble using
        ``NoseHooverChainNVT`` integration.

        Parameters
        ----------
        calculator : str, optional
            The ASE calculator to use for force and energy evaluation
            (default: ``'EMT'``).
        distribution : callable, optional
            Function used to initialize velocities (default:
            ``MaxwellBoltzmannDistribution``).

        Returns
        -------
        ResultMD
            An object containing the simulation data.

        Notes
        -----
        If ``create_trajectory`` is ``True`` Trajectory snapshots are written to
        a `.traj` file with the chemical symbols of the system as the filename.
        Otherwise the snapshots will be written to a :class:`~ResultMD`
        """

        try:
            self._add_distribution(distribution)
            self.crystal.calc = self._check_calculator(calculator, calc_params)

            dyn = NoseHooverChainNVT(
                self.crystal,
                timestep=self.timestep,
                temperature_K=self.temperature,
                tdamp=self.thermo_time,
            )
            self._attach_outputs(dyn, print)

            dyn.run(self.length)
        except IOError as e:
            logger.error(e)
            raise IOError("Failed to write trajectory file.") from e
        except Exception as e:
            logger.error(e)
            raise
        return ResultMD(self.result)
