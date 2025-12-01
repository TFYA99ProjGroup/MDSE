import ase.io
from ase import Atoms, units
from asap3.md.verlet import VelocityVerlet
from asap3 import LennardJones, Trajectory, EMT
from ase.build import bulk
from ase.visualize import view
from ase.md.nose_hoover_chain import IsotropicMTKNPT
from asap3.md.nose_hoover_chain import NoseHooverChainNVT
from ase.md.velocitydistribution import MaxwellBoltzmannDistribution, Stationary
from ase.parallel import DummyMPI
from asap3 import EMTMetalGlassParameters
from pathlib import Path
import re
from functools import reduce
import math

import logging
import numpy as np
from mdse.md.resultMD import ResultMD

logger = logging.getLogger(__name__)

# This global variable should store the instance of MACECalculator,
# since the constructor of this is SLOW we only want to do it once
the_mace_calculator = None


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

    def __init__(self, config):
        """
        Initialize a molecular dynamics simulation instance.

        This constructor sets up a crystal structure and initializes
        molecular dynamics parameters (simulation, ensemble, and crystal setup)
        from the given configuration dictionary.

        The crystal can be created in one of three ways:
        - **BULK**: Generates a bulk crystal using ASE's `bulk()` function.
        - **FILE**: Loads a crystal structure from a file using ASE I/O.
        - **LIST**: Manually defines atoms from provided symbols, positions,
          and cell parameters.

        Simulation parameters such as timestep, total length, trajectory saving
        intervals, and calculator type are also initialized. Ensemble parameters
        (e.g., NVE, NVT, NPT) are parsed to configure temperature, pressure,
        and thermostat/barostat relaxation times.

        Parameters
        ----------
        config : dict
            Configuration dictionary containing simulation setup parameters.
            This must be structured according to the standard.
        """

        logger.debug("Initialize an instance of SimulateMD")
        crystal_params = config.get("CRYSTAL")

        try:
            crystal_type = crystal_params["TYPE"]
            logger.debug(f"Initialize the crystal from {crystal_type}")

            # We either create our crystal as a bulk crystal, ...
            if crystal_type == "BULK":
                self._check_keys(
                    "CRYSTAL",
                    crystal_params,
                    ["Name", "Structure", "Lattice_a", "Cubic"],
                )

                self.crystal_conv = bulk(
                    crystal_params.get("Name"),
                    crystal_params.get("Structure"),
                    a=crystal_params.get("Lattice_a"),
                    b=crystal_params.get("Lattice_b", None),
                    c=crystal_params.get("Lattice_c", None),
                    cubic=crystal_params.get("Cubic"),
                )

                self.crystal = (self.crystal_conv *
                crystal_params.get("Supercell", (1, 1, 1)))

            # ... or from some standard file format, ...
            elif crystal_type == "FILE":
                self._check_keys("CRYSTAL", crystal_params, ["Filepath"])

                self.crystal_conv = ase.io.read(
                    crystal_params.get("Filepath")
                )

                self.crystal = (self.crystal_conv*
                                crystal_params.get("Supercell", (1,1,1)))

            # ... or by specifying each atom individually
            elif crystal_type == "LIST":
                self._check_keys(
                    "CRYSTAL", crystal_params, ["Symbols", "Positions", "Cell", "Pcb"]
                )
                self.crystal = Atoms(
                    symbols=crystal_params.get("Symbols"),
                    positions=crystal_params.get("Positions"),
                    cell=crystal_params.get("Cell"),
                    pbc=crystal_params.get("Pcb"),
                ) * crystal_params.get("Supercell", (1, 1, 1))
            else:
                raise NotImplementedError()

        except Exception as e:
            logger.error("Error while creating inital crystal:")
            logger.error(e)
            raise RuntimeError(e)

        try:
            # Parameters related to the simulation
            simulation_params = config["SIMULATION"]
            self._check_keys(
                "SIMULATION",
                simulation_params,
                ["Timestep", "Length", "TrajInterval", "Calculator"],
            )
            self.timestep = simulation_params.get("Timestep") * units.fs
            self.length = simulation_params.get("Length")
            self.traj_interval = simulation_params.get("TrajInterval")
            self.calculator = simulation_params.get("Calculator")
            self.calc_params = simulation_params.get("CalculatorParams", {}).copy()
            self.create_trajectory = simulation_params.get("Create_traj", False)

        except Exception as e:
            logger.error("Error parameter values")
            logger.error(e)
            raise RuntimeError(e)

        try:
            # Ensamble parameters
            ensamble_params = config["ENSAMBLE"]
            ensamble_type = ensamble_params["Ensamble"]
            self.ensamble = ensamble_type
            logger.debug(f"Using ensamble: {ensamble_type}")
            if ensamble_type == "NVE":
                self._check_keys("ENSAMBLE", ensamble_params, ["Temp"])
                self.temperature = ensamble_params.get("Temp")

            elif ensamble_type == "NVT":
                self._check_keys("ENSAMBLE", ensamble_params, ["Temp", "ThermoTime"])
                self.temperature = ensamble_params.get("Temp")
                self.thermo_time = ensamble_params.get("ThermoTime")

            elif ensamble_type == "NPT":
                self._check_keys(
                    "ENSAMBLE",
                    ensamble_params,
                    ["Temp", "Pressure", "ThermoTime", "BaroTime"],
                )
                self.temperature = ensamble_params.get("Temp")
                self.pressure_au = ensamble_params.get("Pressure")
                self.thermo_time = ensamble_params.get("ThermoTime")
                self.baro_time = ensamble_params.get("BaroTime")
            else:
                raise NotImplementedError()
        except Exception as e:
            logger.error("Error ensamble values")
            logger.error(e)
            raise RuntimeError(e)
        try:
            self.crystal.calc = self._check_calculator()
        except Exception as e:
            logger.error("Failed to check the calculator: {e}")
            raise RuntimeError(e)
        self.crystal.info["dt"] = self.timestep
        logger.debug("Start saving single_atom_energy info to .info[]")
        E_atom = self.single_atom_energy()
        # E_atom, n_atoms = self.single_atom_energy()
        self.crystal.info["E_single_atom"] = E_atom
        # self.crystal.info["atoms_per_unit"] = n_atoms
        logger.debug("Saved single_atom_energy info succesfull")
        self.result = [self.crystal.copy()]

        self.result[0].info["pot_energy"] = self.crystal.get_potential_energy()
        #self.result[0].info["lattice_frames"] = self.estimate_lattice()
        #self.result[0].info["Structure"] = self.crystal_struct

        logger.debug("Init done")

    def view_super_crystal(self):
        """
        Visualize a supercell of the constructed crystal (3x3x3 as default).

        Notes
        -----
        Requires ASE's `view` function to be available.
        """
        logger.debug("Viewing super crystal")
        try:
            super_crystal = self.crystal
            view(super_crystal)
        except Exception:
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
            logger.info(
                f"Energy per atom: Epot ={epot:6.3f}eV  Ekin = {ekin:.3f}eV "
                f"(T={temp:.3f}K) Etot = {epot + ekin:.3f}eV"
            )
        except Exception as e:
            raise RuntimeError(
                "Energy calculation failed. Ensure calculator is attached."
            ) from e

    def _check_keys(self, name, d, keys):
        missing = [k for k in keys if k not in d]
        if missing:
            raise KeyError(f"Missing keys in {name}: {missing}")

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
            world = DummyMPI()
            distribution(self.crystal, temperature_K=self.temperature, comm=world)
            Stationary(self.crystal)
        except Exception as e:
            raise RuntimeError("Failed to apply velocity distribution.") from e

    def _check_calculator(self):
        """
        Validate and initialize an ASE calculator.

        This method checks whether a valid calculator has been specified and returns
        an initialized instance accordingly. If no calculator is provided, the EMT
        (Effective Medium Theory) calculator is used by default.

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
        if self.calculator == "EMT":
            if self.calc_params.get("use_glass"):
                calculator = EMT(EMTMetalGlassParameters())
            else:
                calculator = EMT(**self.calc_params)
        elif self.calculator == "LennardJones":
            for key in self.calc_params.keys():
                if key == "elements":
                    continue
                self.calc_params[key] = np.array(self.calc_params[key])
            self._check_keys(
                "CalcParams", self.calc_params, ["elements", "epsilon", "sigma", "rCut"]
            )
            calculator = LennardJones(**self.calc_params)
        elif self.calculator == "MACE":
            from mace.calculators import MACECalculator

            logger.debug("We want to use mace!")
            global the_mace_calculator

            if the_mace_calculator is None:
                logger.debug("First time we set a MACE calculator")
                logger.debug("Trying to get MACE model weights from: ")
                logger.debug(Path(self.calc_params.get("model_paths")).resolve())
                the_mace_calculator = MACECalculator(**self.calc_params)
            else:
                logger.debug("NOT first time we create with mace")

            calculator = the_mace_calculator
        else:
            error_msg = (
                f"Calculator {self.calculator} not implemented, "
                "valid calculators are: EMT, LennardJones, MACE"
            )
            raise NotImplementedError(error_msg)

        return calculator

    def _attach_frame(self):
        self.result.append(self.crystal.copy())
        self.result[-1].info["pot_energy"] = self.crystal.get_potential_energy()

    def _attach_outputs(self, dyn, print):
        """Attach outputs to simulation."""
        symbols = "".join(set(self.crystal.get_chemical_symbols()))
        if self.create_trajectory:
            traj = Trajectory(f"{symbols}_{self.temperature}.traj", "w", self.crystal)
            dyn.attach(traj.write, interval=self.traj_interval)

        if print:
            dyn.attach(self.print_energy, interval=self.traj_interval)

        dyn.attach(self._attach_frame, self.traj_interval)

    def simulate(
        self,
        distribution=MaxwellBoltzmannDistribution,
        print=False,
    ):
        """
        Run a molecular dynamics simulation for the selected ensemble.

        This method acts as a high-level dispatcher that selects and executes
        the appropriate simulation routine based on ``self.ensamble``.
        Supported ensembles are:
        - ``NVE``: microcanonical (constant energy)
        - ``NVT``: canonical (constant temperature)
        - ``NPT``: isothermal-isobaric (constant pressure and temperature)

        Parameters
        ----------
        distribution : callable, optional
            Function used to initialize particle velocities.
            Defaults to ``MaxwellBoltzmannDistribution``.
        print : bool, optional
            If ``True``, prints simulation output at runtime.
            Defaults to ``False``.

        Returns
        -------
        ResultMD
            Object containing the trajectory and simulation data.

        Raises
        ------
        ValueError
            If ``self.ensamble`` is not one of ``NVE``, ``NVT``, or ``NPT``.
        pymongo.errors.ServerSelectionTimeoutError
            If a connection to the MongoDB server fails (depending on context).
        Exception
            Propagates other unexpected errors from lower-level methods.

        Notes
        -----
        The ensemble type is read from the instance attribute ``self.ensamble``.
        This attribute must be one of ``'NVE'``, ``'NVT'``, or ``'NPT'``.

        The simulation is carried out using one of:
        - :meth:`simulate_nve`
        - :meth:`simulate_nvt`
        - :meth:`simulate_npt`
        """
        if self.ensamble.lower() == "nve":
            result = self.simulate_nve(distribution, print)
        elif self.ensamble.lower() == "nvt":
            result = self.simulate_nvt(distribution, print)
        elif self.ensamble.lower() == "npt":
            result = self.simulate_npt(distribution, print)
        else:
            msg = f"Not supperted ensamble tried to be used: {self.ensamble} "
            "Please use one of following: NVE, NVT, NPT"
            logger.error(msg)
            raise ValueError(msg)
        return result

    def simulate_nve(
        self,
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
        self.result[0].info["calc"] = self.calculator
        return ResultMD(self.result, self.crystal_conv, self.calc_params)

    def simulate_npt(
        self,
        distribution=MaxwellBoltzmannDistribution,
        print=False,
    ):
        """
        Run a molecular dynamics simulation in the NPT ensemble using
        ``IsotropicMTKNPT`` integration.

        Parameters
        ----------
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
        self.result[0].info["p_au"] = self.pressure_au
        self.result[0].info["calc"] = self.calculator
        return ResultMD(self.result, self.crystal_conv, self.calc_params)

    def simulate_nvt(
        self,
        distribution=MaxwellBoltzmannDistribution,
        print=False,
    ):
        """
        Run a molecular dynamics simulation in the NVT ensemble using
        ``NoseHooverChainNVT`` integration.

        Parameters
        ----------
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
        self.result[0].info["calc"] = self.calculator
        return ResultMD(self.result, self.crystal_conv, self.calc_params)

    def single_atom_energy(self):
        """This function returns the energy of a single atom in the structure.
        Used when calculating cohesive energy.

        returns:
            E_atom (float): The energy of one atom in the structure
            int: How many atoms in formula. Ex MgCu2 gives 3
        """
        logger.debug("Start calculating single_atom energies")

        # Get chemical formula of the "super" crystal
        formula_super = self.crystal.get_chemical_formula()

        # Get "lowest" chemical formula. Ie Na4Cl4 -> NaCl
        matches = re.findall(r"([A-Z][a-z]*)(\d*)", formula_super)
        counts = {el: int(n) if n else 1 for el, n in matches}

        common_divider = reduce(math.gcd, counts.values())
        formula_unit = {el: n // common_divider for el, n in counts.items()}
        logger.debug(f"Found following formula: {formula_unit}")

        # store the energy
        E_atom = 0

        # for each element  in the chemical formula, simulate it alone
        for element, n in formula_unit.items():
            calc = self._check_calculator()
            atom = ase.Atoms(
                [element], #list(element): Cu -> ['C','u']
                positions=[(0, 0, 0)],
                cell=[15, 15, 15],
                pbc=False,
            )
            atom.calc = calc

            # add energy weighted by count
            E_atom += atom.get_potential_energy()*n

        # normalize so we return average energy per atom
        tot_nr_of_atoms = sum(formula_unit.values()) #{Cu : 2, Mg : 1} ==> 2+1=3 atoms
        return E_atom / tot_nr_of_atoms  #len(self.crystal)

        logger.debug(
            f"Could not calc single_atom_energy for {formula_unit}."
            "Not implemented for that many atoms, yet"
        )
        return 0, 0

