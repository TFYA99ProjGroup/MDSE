# Copyright (c) 2025 See AUTHORS
#
# This work is licensed under the terms of the MIT license.
# For a copy, see <https://github.com/TFYA99ProjGroup/MDSE/blob/main/LICENSE>.


"""
Post-processing and analysis of molecular dynamics simulation data.

This module defines the `ResultMD` class, which serves as a primary tool for
analyzing the output of molecular dynamics simulations. It acts as a container
for a sequence of simulation frames (ASE Atoms objects) and provides a rich
set of methods to compute various physical properties from the trajectory data.

The `ResultMD` class can be instantiated directly with a list of frames or
loaded from a `.traj` file using the `from_file` classmethod.

Key functionalities include the calculation of:

- **Structural and Transport Properties**:

  - Mean Squared Displacement (MSD)
  - Self-diffusion coefficient
  - Lindemann index
  - Nearest-neighbor distance

- **Thermodynamic Properties**:

  - Isochoric heat capacity
  - Isobaric specific heat and enthalpy
  - Cohesive energy
  - Temperature, pressure, and energy evolution over time

- **Vibrational Properties**:

  - Velocity Autocorrelation Function (VACF)
  - Density of States (DOS)
  - Debye temperature

- **Mechanical Properties**:

  - Elastic constants (C11, C12, C44)
  - Bulk, Shear, and Young's moduli
"""

from matplotlib import pyplot as pl
from scipy import constants
import numpy as np
from asap3 import Trajectory
from ase import units
from asap3 import EMTMetalGlassParameters
from asap3 import EMT, LennardJones
from ase import Atoms
from ase.eos import EquationOfState
from pathlib import Path

import logging

logger = logging.getLogger(__name__)

the_mace_calculator = None


class ResultMD:
    """Class representing the result of a molecular dynamics (MD) simulation.

    This class stores frames from a simulation and provides methods to
    calculate and visualize the mean squared displacement (MSD).
    """

    def __init__(self, data, conv_crystal=None, calc_params=None):
        """Initialize the ResultMD object.

        Parameters
        ----------
        data : list
            List of ASE Atoms objects representing the simulation frames.
        conv_crystal : ase.Atoms, optional
            The conventional (unit) cell of the crystal structure, used for
            lattice constant calculations. Defaults to None.
        calc_params : dict, optional
            Parameters for the ASE calculator, used to re-initialize the
            calculator for post-processing tasks. Defaults to None.
        """
        logger.debug("Initialize ResultMD")

        self.frames = data
        self.frames_in_fs = 50
        self.name = ""
        self.reached_equilibrium = False

        # For calculating lattice constant
        self.crystal_conv = conv_crystal
        self.calc_params = calc_params
        self.crystal_struct = None

        self.dos = None
        logger.debug("Init done")

    @classmethod
    def from_file(cls, filepath):
        """Create a ResultMD object from a trajectory file.

        Parameters
        ----------
        filepath : str
            Path to the trajectory file (e.g., a `.traj` file).

        Returns
        -------
        ResultMD
            An instance of the class containing the trajectory frames.
        """
        logger.debug(f"Creating instances of ResultMD from {filepath}")
        try:
            traj = Trajectory(filepath)
        except Exception as e:
            logger.error(e)
            raise
        return cls([atom for atom in traj])

    def _calc_msd_list(self, frame_skip=0.2):
        """Calculate the mean squared displacement (MSD) for each direction.

        This method computes the MSD as a function of time lag (tau) for the
        x, y, and z components separately. It first skips a fraction of initial
        frames to account for equilibration.

        Parameters
        ----------
        frame_skip : float, optional
            Fraction of initial frames to skip for equilibration. Defaults to 0.2.

        Returns
        -------
        tuple
            A tuple containing:

            - taus_fs (list): Time lags in femtoseconds.
            - MSD_at_tau_x (list): MSD values in the x-direction (Å²).
            - MSD_at_tau_y (list): MSD values in the y-direction (Å²).
            - MSD_at_tau_z (list): MSD values in the z-direction (Å²).
        """
        logger.debug("Beginning calculations for MSD")

        equilibrium_frame = self.check_equilibrium()

        if self.reached_equilibrium:
            nskip = equilibrium_frame
        else:
            nskip = int(frame_skip * len(self.frames))
        frames = self.frames[nskip:]
        positions = np.array([frame.positions for frame in frames])

        # positions[t] gives positions ALL atoms at time t
        # positions[t][i] gives position of atom i, at time t
        # positions[t][i][0] gives position of atom i in x-direction, at time t

        taus = range(
            int(len(frames) * frame_skip),
            len(positions) - int(frame_skip * len(frames)),
        )

        # Comment: This removes very short taus. So short timesteps
        # But we still get the early frames. Nothing to-do with equilibrium

        MSD_at_tau_x = []
        MSD_at_tau_y = []
        MSD_at_tau_z = []

        logger.debug(f"Beggining iteration over tau. Total {len(taus)}")
        for tau in taus:
            MSD_at_all_t_x = []  # Reset per tau
            MSD_at_all_t_y = []  # Reset per tau
            MSD_at_all_t_z = []  # Reset per tau
            for timestep in range(len(positions) - tau):  # timestep != frames.
                # Calculate |ri(t+tau) - ri(t)|^2
                # Array containing displacement on x for ALL atoms, durint t=timestep
                displacement_x = (
                    positions[timestep, :, 0] - positions[timestep + tau, :, 0]
                )
                displacement_y = (
                    positions[timestep, :, 1] - positions[timestep + tau, :, 1]
                )
                displacement_z = (
                    positions[timestep, :, 2] - positions[timestep + tau, :, 2]
                )

                # square and average over all atoms
                MSD_x_t = np.mean(displacement_x**2)
                MSD_y_t = np.mean(displacement_y**2)
                MSD_z_t = np.mean(displacement_z**2)

                # Move to next time-step
                MSD_at_all_t_x.append(MSD_x_t)
                MSD_at_all_t_y.append(MSD_y_t)
                MSD_at_all_t_z.append(MSD_z_t)

            # Average over the time
            MSD_final_x = np.mean(MSD_at_all_t_x)
            MSD_final_y = np.mean(MSD_at_all_t_y)
            MSD_final_z = np.mean(MSD_at_all_t_z)

            MSD_at_tau_x.append(MSD_final_x)
            MSD_at_tau_y.append(MSD_final_y)
            MSD_at_tau_z.append(MSD_final_z)

        # Remeber: Tau is in frames now. Convert to fs
        taus_fs = [tau * self.frames_in_fs for tau in taus]

        return taus_fs, MSD_at_tau_x, MSD_at_tau_y, MSD_at_tau_z

    def calc_msd(self, frame_skip=0.2):
        """Compute the overall mean squared displacement (MSD).

        This method calculates the total MSD, averaged over all three spatial
        directions.

        Parameters
        ----------
        frame_skip : float, optional
            Fraction of initial frames to skip. Passed to :py:meth:`_calc_msd_list`.
            Defaults to 0.2.

        Returns
        -------
        float
            The average MSD value across all directions (Å²).
        """
        logger.debug("Begginning calc_msd")
        _, MSD_x, MSD_y, MSD_z = self._calc_msd_list(frame_skip)
        return np.mean(MSD_x + MSD_y + MSD_z)

    def estimate_nearest_neighbor_distance(self, positions):
        """Estimate average nearest-neighbor distance for one frame.

        Parameters
        ----------
        positions : numpy.ndarray
            A (N, 3) array of atomic positions for N atoms.

        Returns
        -------
        float
            The average nearest-neighbor distance for the given frame (Å).
        """
        diffs = positions[:, np.newaxis, :] - positions[np.newaxis, :, :]
        dists = np.sqrt(np.sum(diffs**2, axis=-1))
        np.fill_diagonal(dists, np.inf)
        nearest = np.min(dists, axis=1)
        return np.mean(nearest)

    def estimate_average_a(self):
        """Estimate the average nearest-neighbor distance over all frames.

        Returns
        -------
        float
            The average nearest-neighbor distance across all frames in the
            trajectory (Å).
        """
        all_a = [
            self.estimate_nearest_neighbor_distance(f.positions) for f in self.frames
        ]
        return np.mean(all_a)

    def calc_lindemann(self, a=None):
        """Compute the global Lindemann parameter.

        The Lindemann index is a measure of structural disorder, defined as the
        root-mean-square displacement divided by the nearest-neighbor distance.

        Parameters
        ----------
        a : float, optional
            Average nearest-neighbor distance (Å). If not provided, it will be
            calculated using `estimate_average_a()`. Defaults to None.

        Returns
        -------
        float
            The dimensionless Lindemann parameter `delta_L`.
        """
        logging.debug("Calculate lindemann")
        if a is None:
            a = self.estimate_average_a()
        msd = self.calc_msd()
        return np.sqrt(msd) / a

    def visualize_msd(self):
        """Visualize the mean squared displacement (MSD) vs. time lag.

        This method generates a plot showing the MSD for the x, y, and z
        directions as a function of the time lag, tau. It is a convenience
        wrapper around `_calc_msd_list`.
        """
        import matplotlib.pyplot as plt

        logger.debug("Beggining visualize_msd")

        taus_fs, MSD_at_tau_x, MSD_at_tau_y, MSD_at_tau_z = self._calc_msd_list()

        plt.figure(figsize=(6, 4))
        plt.plot(taus_fs, MSD_at_tau_x, label="MSD X", marker="o")
        plt.plot(taus_fs, MSD_at_tau_y, label="MSD Y", marker="s")
        plt.plot(taus_fs, MSD_at_tau_z, label="MSD Z", marker="^")

        plt.xlabel("Time lag τ (fs)")
        plt.ylabel("MSD (Å²)")
        plt.title("Mean Squared Displacement vs Time Lag")
        plt.legend()
        plt.grid(True)
        plt.tight_layout()
        plt.show()

    def _calc_vacf(self, frame_skip=0.5, max_lag=0.5):
        """Calculates the velocity autocorrelation function (VACF).

        This method computes the VACF from the atomic velocities stored in
        `self.frames`. It uses the **Wiener-Khinchin theorem** (via FFT)
        for a computationally efficient calculation.

        Parameters
        ----------
        frame_skip : float, optional
            Fraction of the *total* initial frames to skip for equilibration.
            Defaults to 0.5.
        max_lag : float, optional
            Fraction of the *remaining* frames (after skipping) to use as the
            maximum lag time. The returned VACF will have this many points.
            Defaults to 0.5.

        Returns
        -------
        numpy.ndarray
            A 1D array containing the normalized VACF.
        """
        self.check_equilibrium()

        if self.reached_equilibrium:
            nskip = self.check_equilibrium()
        else:
            nskip = int(frame_skip * len(self.frames))
        frames = self.frames[nskip:]
        nframes, _ = np.shape(frames)
        max_lag = int(nframes * max_lag)

        vels = [frame.get_velocities() for frame in frames]
        vels = np.array(vels)

        com_vel = vels.mean(axis=1, keepdims=True)

        vel_rel = vels - com_vel

        vflat = vel_rel.reshape(nframes, -1)
        vflat -= vflat.mean(axis=0, keepdims=True)

        fft_v = np.fft.fft(vflat, axis=0)
        psd = np.real(np.fft.ifft(np.abs(fft_v) ** 2, axis=0))
        vacf = psd.mean(axis=1)
        vacf = vacf[:max_lag]

        vacf /= vacf[0]
        return vacf

    def calc_density_of_states(self, frame_skip=0.5):
        """Calculates the (vibrational) Density of States (DOS).

        This method computes the DOS by taking the Fourier transform of the
        Velocity Autocorrelation Function (VACF), a relationship described
        by the **Wiener-Khinchin theorem**.

        The resulting DOS is cached in ``self.dos``. If this method is called
        again, it will return the cached values without recalculation.

        Parameters
        ----------
        frame_skip : float, optional
            Fraction of the total initial frames to skip for equilibration.
            This value is passed directly to :py:meth:`_calc_vacf`.
            Defaults to 0.5.

        Returns
        -------
        tuple
            A tuple of `(dos, omega)`:

            - **dos** (numpy.ndarray): The 1D array of the normalized\
              density of states.
            - **omega** (numpy.ndarray): The 1D array of the corresponding\
              angular frequencies (in rad/s).
        """
        self.check_equilibrium()
        if self.reached_equilibrium:
            max_lag = self.check_equilibrium()
            frame_skip = max_lag / len(self.frames)
        else:
            max_lag = int(frame_skip * len(self.frames))
        frames = self.frames[max_lag:]
        _, natoms = np.shape(frames)
        dt = frames[0].info["dt"] * 1e-15 / units.fs
        logger.debug(
            (
                ("Calculating density of states for system."),
                (f"frames: {max_lag}, natoms: {natoms}, dt: {dt} fs"),
            ),
        )

        vacf = self._calc_vacf(frame_skip)
        n = len(vacf)

        freqs = np.fft.rfftfreq(n, d=dt)
        omega = 2 * np.pi * freqs

        if self.dos is None:
            logger.debug("DOS not yet calculated")
            spectrum = np.fft.rfft(vacf) * dt

            dos = np.real(spectrum)

            area = np.trapz(dos, x=omega)
            target = 3.0 * natoms

            dos *= target / area
            dos = np.maximum(dos, 0)

            self.dos = dos
        else:
            logger.debug("DOS already calculated")

        return self.dos, omega

    def plot_density_of_states(self):
        """Visualize the density of states (DOS).

        This method plots the cached DOS as a function of angular frequency.
        :py:meth:`calc_density_of_states` must be called first to compute and cache
        the DOS data.
        """
        pl.figure()
        pl.plot(self.dos)
        pl.show()

    def calc_debye_temperature(self, frame_skip=0.5):
        """Calculates the Debye temperature.

        This method estimates the Debye temperature by first finding the
        Debye frequency from the (vibrational) Density of States (DOS).

        The Debye frequency is defined as the frequency cutoff
        required for the total number of vibrational modes to equal the
        system's total degrees of freedom. It is found by solving the following
        equation:

        .. math::
            \\int_{0}^{\\omega_D} DOS(\\omega) d\\omega = 3N

        The calculation performs the following steps:

        1. Calls :py:meth:`calc_density_of_states` to get the `dos` \
            and angular frequency :math:`\\omega` arrays.
        2. Calculates the cumulative integral of the DOS with respect to \
            :math:`\\omega` (i.e., the total number of modes up to a given frequency).
        3. Finds the index where this cumulative integral first matches or \
            exceeds the target degrees of freedom (3N).
        4. The frequency at this index is taken as the Debye frequency.
        5. Converts the Debye frequency to the Debye temperature using the relation

            .. math::
                \\Theta_D = \\frac{\\hbar \\omega_D}{k_B}.

        Parameters
        ----------
        frame_skip : float, optional
            Fraction of the total initial frames to skip for equilibration.
            This value is passed directly to `calc_density_of_states`.
            Defaults to 0.5.

        Returns
        -------
        float
            The calculated Debye temperature (:math:`\\Theta_D`) in Kelvin.
        """
        kB = constants.Boltzmann
        hbar = constants.hbar
        _, natoms = np.shape(self.frames)

        equilibrium_frame = self.check_equilibrium()
        if self.reached_equilibrium:
            frame_skip = equilibrium_frame / len(self.frames)

        dos, omega = self.calc_density_of_states(frame_skip)

        cum_int = np.cumsum(0.5 * (dos[1:] + dos[:-1]) * (omega[1:] + omega[:-1]))

        target = 3.0 * natoms

        if cum_int[-1] < target:
            logger.error("DOS integral not correct", exc_info=True)

        idx = np.searchsorted(cum_int, target)
        if idx == 0:
            omega_D = omega[1]
        else:
            omega_D = omega[idx]

        Theta_D = (hbar * omega_D) / kB

        return Theta_D

    def calc_self_diff(self):
        """Calculate the self-diffusion coefficient from the MSD.

        The diffusion coefficient (D) is determined from the slope of the mean
        squared displacement (MSD) vs. time lag (:math:`\\tau`) plot, based on
        the Einstein relation in 3D:

        .. math::
            MSD(\\tau) = 6D\\tau

        A linear regression is performed on a central portion of the MSD data
        to find the slope.

        Returns
        -------
        float
            The total self-diffusion coefficient in units of Å² per unit of
            time from the simulation (e.g., Å²/fs).
        """
        taus_fs, MSD_of_tau_x, MSD_of_tau_y, MSD_of_tau_z = self._calc_msd_list()
        if taus_fs == []:
            return 0
        # Filter out noisy start/end, 10%
        """
        if self.reached_equilibrium:
            filter_start = self.check_equilibrium()
        else:
            filter_start = int(len(MSD_of_tau_x) * 0.1)"""
        filter_start = (
            0  # should already have filtered out first bad frames in calc_msd
        )
        filter_end = int(len(MSD_of_tau_x) * 0.9)

        MSD_of_tau_x = MSD_of_tau_x[filter_start:filter_end]
        MSD_of_tau_y = MSD_of_tau_y[filter_start:filter_end]
        MSD_of_tau_z = MSD_of_tau_z[filter_start:filter_end]

        taus_fs = taus_fs[filter_start:filter_end]

        # Now need to plot MDS(tau) vs tau, slope is here related to D
        from scipy.stats import linregress

        D_slope_x = linregress(taus_fs, MSD_of_tau_x)
        D_slope_y = linregress(taus_fs, MSD_of_tau_y)
        D_slope_z = linregress(taus_fs, MSD_of_tau_z)

        # Calc D in each dimension
        Dx = D_slope_x.slope / (2)
        Dy = D_slope_y.slope / (2)
        Dz = D_slope_z.slope / (2)

        # Calc total D
        D_total = (Dx + Dy + Dz) / 3

        return D_total

    def calc_isobaric_enthalpy(self):
        """Calculates isobaric enthalpy after a NPT ensemble.

        The enthalpy (H) is calculated as:

        .. math::
            H = E + PV

        where E is the total
        energy (potential + kinetic), P is the pressure, and V is the volume.

        Returns
        -------
        numpy.ndarray
            An array of enthalpy values for each frame in Joules.

        Note
        -------
            Developers, you need a calc to get the total energy. Btw,
            if you just began reading theese docs, calc stands for calculator.
        """
        E_eV, V_A3 = [], []

        pressure = self.get_pressures()
        p_au = np.mean(pressure)

        p_Pa = p_au * (constants.eV / (constants.angstrom**3))

        logger.debug(f"au_to_Pa: {constants.eV / (constants.angstrom**3)}")

        # Check if potential energy is saved. If not, calculate it
        self._attach_pot_energy_to_frames()

        for frame in self.frames:
            E_eV.append(frame.info["pot_energy"] + frame.get_kinetic_energy())
            V_A3.append(frame.get_volume())

        E_J = np.array(E_eV) * constants.eV
        V_m3 = np.array(V_A3) * (constants.angstrom**3)

        logger.debug(f"ev_to_J: {constants.eV}")
        logger.debug(f"angstrom: {constants.angstrom}")

        enthalpy_J = E_J + p_Pa * V_m3
        logger.debug(f"enthalpy {enthalpy_J}")
        return enthalpy_J

    def calc_isobaric_specific_heat(self):
        """Calculate the isobaric specific heat (Cp) per unit mass.

        This method is intended for results from an NPT ensemble. It
        calculates Cp from the fluctuations in enthalpy (H) using the formula:

        .. math::
            C_p = \\frac{\\langle (H - \\langle H \\rangle)^2 \\rangle}{k_B T^2}

        Returns
        -------
        float
            The isobaric specific heat in units of J / (kg * K).
        """
        T_K = []
        for frame in self.frames:
            T_K.append(frame.get_temperature())

        T_K = np.mean(T_K)

        H_J = self.calc_isobaric_enthalpy()

        self.check_equilibrium()

        if self.reached_equilibrium:
            frame_skips = self.check_equilibrium() / len(self.frames)
        else:
            frame_skips = 0.5
        nskip = int(len(H_J) * frame_skips)
        # Skip the part of the simulation before equilibration
        H_J = H_J[nskip:]

        varH = np.var(H_J)
        # Isobaric heat capacity
        Cp = varH / (constants.value("Boltzmann constant") * T_K**2)

        logger.debug(f"boltzmann: {constants.value('Boltzmann constant')}")

        m_u = self.frames[0].get_masses()
        tot_mass_u = m_u.sum()
        tot_mass_kg = tot_mass_u * constants.atomic_mass

        logger.debug(f"atomic_mass: {constants.atomic_mass}")

        return Cp / tot_mass_kg

    def calc_isochoric_heat_capacity_per_atom(self):
        """Calculate the isochoric heat capacity (Cv) per atom.

        This method is intended for results from an NVT ensemble. It
        calculates Cv from the fluctuations in total energy (E) using the
        formula:

        .. math::
            C_v = \\frac{\\langle (E - \\langle E \\rangle)^2 \\rangle}{k_B T^2}

        Returns
        -------
        float
            The isochoric heat capacity per atom in units of J/K per atom.
        """
        E_eV, T_K = [], []

        # Check if potential energy is saved. If not, calculate it
        self._attach_pot_energy_to_frames()

        for frame in self.frames:
            E_eV.append(frame.info["pot_energy"] + frame.get_kinetic_energy())
            T_K.append(frame.get_temperature())

        E_J = np.array(E_eV) * constants.eV
        T_K = np.mean(T_K)

        self.check_equilibrium()

        if self.reached_equilibrium:
            frame_skips = self.check_equilibrium() / len(self.frames)
        else:
            frame_skips = 0.5
        nskip = int(len(E_J) * frame_skips)
        # Skip the part of the simulation before equilibration
        E_J = E_J[nskip:]

        varE = np.var(E_J)

        Cv = varE / (constants.value("Boltzmann constant") * T_K**2)

        n_atoms = len(self.frames[0])

        return Cv / n_atoms

    def _energy_with_strain(self, crystal, strain_matrix):
        """Helper function to calculate potential energy of a strained crystal.

        Parameters
        ----------
        crystal : ase.Atoms
            The Atoms object to be strained.
        strain_matrix : numpy.ndarray
            A 3x3 matrix representing the strain to apply to the cell.

        Returns
        -------
        float
            The potential energy of the strained crystal in Joules.
        """
        logger.debug("calc strained energy")
        crystal.calc = self._check_calc_2()
        cell = crystal.cell.copy()

        strained_cell = (np.eye(3) + strain_matrix) @ cell
        crystal.set_cell(strained_cell, scale_atoms=True)
        logger.debug("calc strained energy complete!")
        return crystal.get_potential_energy() * constants.eV

    def calc_C11(self, crystal_equil, epsilon=0.01):
        """Calculate the C11 elastic constant.

        C11 is calculated by applying a uniaxial strain :math:`\\epsilon_{xx}` and using
        a finite difference approximation for the second derivative of energy.

        Parameters
        ----------
        crystal_equil : ase.Atoms
            A relaxed equilibrium structure. A calculator will be attached
            inside the function.
        epsilon : float, optional
            Magnitude of the applied strain. Defaults to 0.01.

        Returns
        -------
        float
            The C11 elastic constant in Pascals.
        """
        logger.debug("Calculating C11")
        crystal_equil.calc = self._check_calc_2()
        volume = crystal_equil.get_volume() * (constants.angstrom**3)

        compression = np.array([[epsilon, 0, 0], [0, 0, 0], [0, 0, 0]])

        E0 = crystal_equil.get_potential_energy() * constants.eV
        E_plus = self._energy_with_strain(crystal_equil.copy(), compression)
        E_minus = self._energy_with_strain(crystal_equil.copy(), -compression)

        deriv = (E_plus + E_minus - 2 * E0) / (epsilon**2)

        C11 = deriv / volume
        logger.debug(f"C11: {C11}")

        return C11

    def calc_C12(self, crystal_equil, epsilon=0.01):
        """Calculate the C12 elastic constant.

        C12 is calculated by applying a biaxial strain
        (:math:`\\epsilon_{xx} = \\epsilon`, :math:`\\epsilon_{yy} = -\\epsilon`) and
        using a finite difference approximation.

        Parameters
        ----------
        crystal_equil : ase.Atoms
            A relaxed equilibrium structure. A calculator will be attached
            inside the function.
        epsilon : float, optional
            Magnitude of the applied strain. Defaults to 0.01.

        Returns
        -------
        float
            The C12 elastic constant in Pascals.
        """
        logger.debug("Caluculating C12")
        crystal_equil.calc = self._check_calc_2()
        volume = crystal_equil.get_volume() * (constants.angstrom**3)

        compression = np.array([[epsilon, 0, 0], [0, -epsilon, 0], [0, 0, 0]])

        E0 = crystal_equil.get_potential_energy() * constants.eV
        E_plus = self._energy_with_strain(crystal_equil.copy(), compression)
        E_minus = self._energy_with_strain(crystal_equil.copy(), -compression)

        deriv = (E_plus + E_minus - 2 * E0) / (epsilon**2)

        C12 = deriv / volume
        logger.debug(f"C12: {C12}")

        return C12

    def calc_C44(self, crystal_equil, gamma):
        """Calculate the C44 elastic constant.

        C44 is calculated by applying a shear strain (:math:`\\epsilon_{xy}`) and using
        a finite difference approximation.

        Parameters
        ----------
        crystal_equil : ase.Atoms
            A relaxed equilibrium structure. A calculator will be attached
            inside the function.
        gamma : float
            Magnitude of the applied shear strain.

        Returns
        -------
        float
            The C44 elastic constant in Pascals.
        """
        logger.debug("C44")
        crystal_equil.calc = self._check_calc_2()
        volume = crystal_equil.get_volume() * (constants.angstrom**3)

        def energy_with_shear_strain(crystal, gamma):
            crystal.calc = self._check_calc_2()
            cell = crystal.cell.copy()
            shear = np.array([[0, gamma / 2, 0], [gamma / 2, 0, 0], [0, 0, 0]])
            shear_cell = (np.eye(3) + shear) @ cell
            crystal.set_cell(shear_cell, scale_atoms=True)
            return crystal.get_potential_energy() * constants.eV

        shear = np.array([[0, gamma / 2, 0], [gamma / 2, 0, 0], [0, 0, 0]])

        E0 = crystal_equil.get_potential_energy() * constants.eV
        E_plus = self._energy_with_strain(crystal_equil.copy(), shear)
        E_minus = self._energy_with_strain(crystal_equil.copy(), -shear)

        deriv = (E_plus + E_minus - 2 * E0) / (gamma**2)

        C44 = deriv / volume
        logger.debug(f"C44: {C44}")

        return C44

    def calc_shear_modulus(self, strain=0.01):
        """Calculate the shear modulus (G) for a cubic crystal.

        This method computes the Voigt, Reuss, and Hill averages for the shear
        modulus based on the calculated elastic constants C11, C12, and C44.
        It returns the Hill average, which is the arithmetic mean of the Voigt
        (upper bound) and Reuss (lower bound) moduli.

        Parameters
        ----------
        strain : float, optional
            Magnitude of the strain applied for calculating the underlying
            elastic constants. Defaults to 0.01.

        Returns
        -------
        float
            The Hill average shear modulus in Pascals.
        """
        ## Maybe fix mean over serveral equil frames
        logger.debug("Calculating shear moudulus")
        equil_frame = self.check_equilibrium()

        C44, C11, C12 = [], [], []
        for frame in self.frames[equil_frame:]:
            crystal_equil = frame.copy()
            C44.append(self.calc_C44(crystal_equil, strain))
            C11.append(self.calc_C11(crystal_equil, strain))
            C12.append(self.calc_C12(crystal_equil, strain))

        C44 = np.mean(C44)
        C11 = np.mean(C11)
        C12 = np.mean(C12)

        # Voight gives an upper bound of the shear modulus
        shear_modulus_voight = (3 * C44 + C11 - C12) / 5

        # Reuss gives a lower bound of the shear modulus
        shear_modulus_reuss = 5 * (C11 - C12) * C44 / (4 * C44 + 3 * (C11 - C12))

        # Hill average of the Voight and Reuss shear modulus
        shear_modulus = (shear_modulus_reuss + shear_modulus_voight) / 2
        logger.debug(f"shear modulus: {shear_modulus}")
        return shear_modulus

    def calc_bulk_modulus(self, strain=0.01):
        """Calculate the bulk modulus (B) for a cubic crystal.

        The bulk modulus is calculated from the elastic constants C11 and C12
        using the relation:

        .. math::
            B = \\frac{C_{11} + 2C_{12}}{3}

        Parameters
        ----------
        strain : float, optional
            Magnitude of the strain applied for calculating the underlying
            elastic constants. Defaults to 0.01.

        Returns
        -------
        float
            The bulk modulus in Pascals.
        """
        logger.debug("Calculating bulk modulus")
        equil_frame = self.check_equilibrium()

        C11, C12 = [], []

        for frame in self.frames[equil_frame:]:
            crystal_equil = frame.copy()
            C11.append(self.calc_C11(crystal_equil, strain))
            C12.append(self.calc_C12(crystal_equil, strain))

        C11 = np.mean(C11)
        C12 = np.mean(C12)

        bulk_modulus = (C11 + 2 * C12) / 3

        logger.debug(f"bulk_modulus: {bulk_modulus}")
        return bulk_modulus

    def calc_youngs_modulus(self, strain=0.01):
        """Calculate Young's modulus (E).

        Young's modulus is calculated from the bulk (B) and shear (G) moduli
        using the relation:

        .. math::
            E = \\frac{9BG}{3B + G}

        Parameters
        ----------
        strain : float, optional
            Magnitude of the strain applied for calculating the underlying
            bulk and shear moduli. Defaults to 0.01.

        Returns
        -------
        float
            Young's modulus in Pascals.
        """
        logger.debug("Calculating Young's modulus")

        B = self.calc_bulk_modulus(strain)
        G = self.calc_shear_modulus(strain)

        youngs_modulus = 9 * B * G / (3 * B + G)

        logger.debug(f"Young's modulus: {youngs_modulus}")
        return youngs_modulus

    def get_pot_energies(self):
        """Get the potential energy for each frame.

        If potential energy was not saved during the simulation, this method
        will calculate it for all frames.

        Returns
        -------
        list
            A list of potential energy values (eV) for each frame.
        """
        # Check if pot_energy is calculated. If not, calculates it
        self._attach_pot_energy_to_frames()
        return [frame.info["pot_energy"] for frame in self.frames]

    def get_kin_energies(self):
        """Get the kinetic energy for each frame.

        Returns
        -------
        list
            A list of kinetic energy values (eV) for each frame.
        """
        logger.debug("Get kinetic energies")
        return [frame.get_kinetic_energy() for frame in self.frames]

    def get_tot_energies(self):
        """Get the total energy (potential + kinetic) for each frame.

        Returns
        -------
        list
            A list of total energy values (eV) for each frame.
        """
        logger.debug("Get total energies")

        # Check if potential energy is saved. If not, calculate it
        self._attach_pot_energy_to_frames()
        return [
            frame.get_kinetic_energy() + frame.info["pot_energy"]
            for frame in self.frames
        ]

    def get_time_axis(self):
        """Generate a time axis for the simulation frames.

        Returns
        -------
        numpy.ndarray
            An array of time values corresponding to each frame, in the same
            time units as the simulation timestep (e.g., fs).
        """
        logger.debug("Get an time-axis")
        dt = self.frames[0].info["dt"]
        times = np.arange(len(self.frames)) * dt
        return times

    def _attach_pot_energy_to_frames(self):
        """Ensure potential energy is calculated and stored in each frame.

        This helper method checks if `pot_energy` is already in `frame.info`.
        If not, it initializes the calculator and computes the potential energy
        for every frame, storing the result in `frame.info['pot_energy']`.
        """
        logger.debug("Potential energy was needed, check if stored in frames")
        # Check if SM saved potential energy
        if "pot_energy" in self.frames[0].info:
            logger.debug("Potential energy already saved in frames")
            return

        logger.debug("No potential energy was saved in frames, calc. it")
        # No pot energy was saved, need to init calculator and re-calculate
        calculator = self._check_calc_2()
        for frame in self.frames:
            frame.calc = calculator
            frame.info["pot_energy"] = frame.get_potential_energy()
        logger.debug("pot_energy was added to all frames")

    def single_atom_energy(self):
        """Calculate the average potential energy of isolated atoms.

        This method calculates the total potential energy of the individual,
        non-interacting atoms that make up the material's formula unit. The
        result is then averaged per atom in the formula unit. This value is
        a key component for calculating the cohesive energy.

        Returns
        -------
        float
            The average potential energy per isolated atom (eV).
        """
        logger.debug("Start calculating single_atom energies")

        # Get chemical formula of the "super" crystal
        import re
        from functools import reduce
        import math

        formula_super = self.frames[0].get_chemical_formula()

        # Get "lowest" chemical formula. Ie Na4Cl4 -> NaCl
        matches = re.findall(r"([A-Z][a-z]*)(\d*)", formula_super)
        counts = {el: int(n) if n else 1 for el, n in matches}

        common_divider = reduce(math.gcd, counts.values())
        formula_unit = {el: n // common_divider for el, n in counts.items()}
        logger.debug(f"Found following formula: {formula_unit}")

        # store the energy
        E_atom = 0
        calc = self._check_calc_2()

        # If EMT with paramater, first attachment must be to compound,
        # not single element.
        # Will crash otherwise
        if self.calculator == "EMT" and self.calc_params.get("use_glass"):
            el_tot = list(formula_unit.keys())
            dummy_atom = Atoms(
                el_tot,
                positions=[(i * 1, 0, 0) for i in range(len(el_tot))],
                cell=[5, 5, 5],
                pbc=False,
            )
            dummy_atom.calc = calc

        # for each element  in the chemical formula, simulate it alone
        for element, n in formula_unit.items():
            atom = Atoms(
                [element],  # list(element): Cu -> ['C','u']
                positions=[(0, 0, 0)],
                cell=[15, 15, 15],
                pbc=False,
            )
            atom.calc = calc

            # add energy weighted by count
            E_atom += atom.get_potential_energy() * n

        # normalize so we return average energy per atom
        tot_nr_of_atoms = sum(formula_unit.values())  # {Cu : 2, Mg : 1} ==> 2+1=3 atoms
        return E_atom / tot_nr_of_atoms  # len(self.crystal)

    def get_cohesive_energy(self):
        """Calculate the cohesive energy per atom.

        Cohesive energy is the energy required to separate a material into
        isolated, neutral atoms. It is calculated as:

        .. math::
            E_{\\text{cohesive}} = E_{\\text{isolated}} - E_{\\text{bulk}}

        where :math:`E_{\\text{isolated}}` is the average energy of an isolated atom and
        :math:`E_{\\text{bulk}}`
        is the average potential energy per atom in the bulk material.

        Returns
        -------
        float
            The cohesive energy per atom (eV).
        """
        logger.debug("Calc cohesive energy")
        pots = self.get_pot_energies()
        equil_frame = self.check_equilibrium()
        if not self.reached_equilibrium:
            equil_frame = 7

        return self.single_atom_energy() - (
            np.mean(pots[equil_frame:]) / len(self.frames[0])
        )

    def get_temperatures(self):
        """Get the temperature for each frame.

        Returns
        -------
        list
            A list of temperature values (K) for each frame.
        """
        logger.debug("Get tempertures")
        return [frame.get_temperature() for frame in self.frames]

    def get_pressures(self):
        """Get the pressure for each frame.

        Returns
        -------
        list
            A list of pressure values for each frame, calculated from the
            stress tensor.
        """
        pressure = []
        for frame in self.frames:
            pressure.append(self.get_pressure(frame))

        return pressure

    def get_pressure(self, frame):
        """Get pressure for a single frame.

        Pressure is calculated as the negative average of the diagonal elements of the
        stress tensor:

        .. math::
            P = - \\frac{\\sigma_{xx} + \\sigma_{yy} + \\sigma_{zz}}{3}

        Parameters
        ----------
        frame : ase.Atoms
            The Atoms object for which to calculate the pressure.

        Returns
        -------
        float
            The pressure of the frame.
        """
        frame.calc = self._check_calc_2()
        stress = frame.get_stress()
        pressure = -(stress[0] + stress[1] + stress[2]) / 3

        return pressure

    def check_equilibrium(self):
        """Check if the simulation has reached equilibrium.

        This method attempts to identify the frame at which the system
        equilibrates by checking for three conditions in order:

        1. Total energy becomes constant.
        2. Temperature becomes constant.
        3. Total energy begins to oscillate around a stable mean.

        It sets `self.reached_equilibrium` to True if any condition is met.

        Returns
        -------
        int
            The index of the first frame considered to be in equilibrium.
            Returns 0 if no equilibrium is detected.
        """
        logger.debug("Started check if equilibrium was reached")
        kin_energy = self.get_kin_energies()
        pot_energy = self.get_pot_energies()
        Tot_energy = [kin + pot for (kin, pot) in zip(kin_energy, pot_energy)]
        temperatures = self.get_temperatures()

        # Too short to check equilibrium
        if len(self.get_kin_energies()) < 10:
            self.reached_equilibrium = False
            logger.debug("Simulation had too few frames. No equilibrium")
            return 0
        # ----Based on total energy-----

        energy_frame = self._check_equilibrium_const(Tot_energy, 0.0001)

        if energy_frame != len(Tot_energy) - 2:  # We found equilibrium
            self.reached_equilibrium = True
            logger.debug("Found equilibrium, energy reaches const value")
            return energy_frame

        # ----Based on temperature-----

        temp_frame = self._check_equilibrium_const(temperatures, 0.001)

        if temp_frame != len(temperatures) - 2:  # We found equilibrium
            self.reached_equilibrium = True
            logger.debug("Found equilibrium, temperature reaches const value")
            return temp_frame

        # ----If oscillating system----

        oscill_frame = self._check_equilibrium_oscill(Tot_energy, 0.005)
        if oscill_frame != len(Tot_energy) - 2:  # We found equilibrium
            self.reached_equilibrium = True
            logger.debug("Found equilibrium, energy oscillates")
            return oscill_frame

        # ----No equilibrium---
        self.reached_equilibrium = False
        logger.debug("No equilibrium was found")
        return 0

    def _check_equilibrium_const(self, property, tol):
        """Check when a property stabilizes around a constant value.

        Equilibrium is assumed when the relative change between consecutive
        data points falls below a given tolerance.

        Parameters
        ----------
        property : list
            A list of numerical values (e.g., energy or temperature) over time.
        tol : float
            The relative tolerance for determining stability.

        Returns
        -------
        int
            The index of the first frame where the property is stable.
        """
        logger.debug("Check if we have equilibrium in the form of constant property")
        difference = [
            abs(property[i + 1] - property[i]) / property[i]
            for i in range(len(property) - 1)
        ]

        for pos, diff in enumerate(difference):
            if diff <= tol:
                break
            else:
                pass

        return pos

    def _check_equilibrium_oscill(self, Tot_energy, tol):
        """Check if a property is oscillating around a stable mean.

        This method uses a moving window to calculate the mean of the property.
        Equilibrium is assumed when the relative change between the means of
        consecutive windows falls below a tolerance.

        Parameters
        ----------
        Tot_energy : list
            List of total energy values for all frames.
        tol : float
            The relative tolerance for determining stability of the window mean.

        Returns
        -------
        int
            The index of the first frame of the first stable window.
        """
        logger.debug("Check if equilibrium, in oscillating behavior")
        window_lenght = 5
        windows = [
            Tot_energy[i : (i + window_lenght)]
            for i in range(0, len(Tot_energy) - window_lenght)
        ]
        # Mean of each window
        windows_means = np.array([sum(win) / len(win) for win in windows])

        diffs = [
            abs(windows_means[i + 1] - windows_means[i]) / windows_means[i]
            for i in range(len(windows_means) - 1)
        ]
        # Find where we start oscillating
        if len(diffs) == 0:
            pos = len(Tot_energy) - 2

        for pos, diff in enumerate(diffs):
            if diff < tol:
                return pos
            else:
                pass

        return len(Tot_energy) - 2

    def _check_keys(self, name, d, keys):
        """Check for the presence of required keys in a dictionary.

        Parameters
        ----------
        name : str
            The name of the dictionary being checked (for error messages).
        d : dict
            The dictionary to check.
        keys : list[str]
            A list of keys that must be present in the dictionary.

        Raises
        ------
        KeyError
            If any of the specified keys are missing from the dictionary.
        """
        missing = [k for k in keys if k not in d]
        if missing:
            raise KeyError(f"Missing keys in {name}: {missing}")

    def _check_calc_2(self):
        """Initialize and return a calculator based on stored parameters.

        This method re-creates the ASE calculator that was used for the
        original simulation, using the type and parameters stored in `self.frames`
        and `self.calc_params`. This is necessary for post-processing
        calculations that require a calculator.

        Returns
        -------
        ase.calculators.calculator.Calculator
            An initialized ASE calculator instance.
        """
        if not self.crystal_conv:
            raise RuntimeError(
                "ResultMD object was not given conventional cell when init."
            )

        self.calculator = self.frames[0].info["calc"]
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

    def _estimate_lattice(self):
        """Calculate energy vs. lattice parameters for the conventional cell.

        This method systematically varies the lattice parameters of the
        conventional cell, calculates the potential energy for each variation,
        and returns the data needed for finding the equilibrium lattice.

        **For systems where we have same constant in all directions:
        Calculate volume at each guess. Then we do a EOS-fit latter to find min.

        **For system where 2 independent constants:
        Calc. energy for each lattice constant guess. Then, latter do a
        quadratic line-fit to find minimum.

        **For systems where 3 independent constants:
        Try changing 1, keeping two other fixed. Find min for this one.
        Then using this min, try guessing for one other direction, find min.
        So will get an estimate of which 3 constants in all directions give min.

        Returns
        -------
        list
            The format of the returned list depends on the crystal structure:
            - For cubic/trigonal: A list of `[energy, volume]` pairs.
            - For hexagonal/tetragonal: A list of `[energy, [a, a, c]]` lists.
            - For orthorhombic/monoclinic/triclinic: A list `[a, b, c]` of the
              optimized lattice constants.

        Notes
        -----
        This method sets `self.crystal_struct` based on the cell geometry.
        """
        logger.debug("Starting estimate_lattice()")
        a0, b0, c0, alfa, beta, gamma = self.crystal_conv.get_cell_lengths_and_angles()

        if alfa == beta == gamma == 90 and a0 == b0 == c0:
            self.crystal_struct = "cubic"
        elif alfa == beta != gamma and a0 == b0 == c0:
            self.crystal_struct = "trigonal"
        elif alfa == beta != gamma and a0 == b0 != c0:
            self.crystal_struct = "hexagonal"
        elif alfa == beta == gamma and a0 == b0 != c0:
            self.crystal_struct = "tetragonal"
        elif alfa == beta == gamma and a0 != b0 != c0:
            self.crystal_struct = "orthorhombic"
        elif alfa == gamma != beta and a0 != b0 != c0:
            self.crystal_struct = "monoclinic"
        elif alfa != beta != gamma and a0 != b0 != c0:
            self.crystal_struct = "triclinic"
        else:
            raise RuntimeError("esimate_lattice() could not determine structure type")

        logger.debug(f"Found structure {self.crystal_struct}")
        conv_atoms = Atoms(
            symbols=self.crystal_conv.get_chemical_symbols(),
            positions=self.crystal_conv.get_positions(),
            cell=self.crystal_conv.get_cell(),
            pbc=True,
        )

        if self.crystal_struct == "cubic" or self.crystal_struct == "triagonal":
            # Same lattice const. in all directions.
            # Find optimal using EOS fit in result
            logger.debug(
                f"Start calculating energy vs volume\
                         for: {self.crystal_struct}"
            )
            cell0 = self.crystal_conv.get_cell()

            a0 = self.crystal_conv.get_cell()[0, 0]

            energy_vs_vol = []

            for scaling in np.linspace(0.95, 1.05, 50):  # increase for better result
                scaled = conv_atoms.copy()
                scaled.set_cell(cell0 * scaling, scale_atoms=True)
                scaled.calc = self._check_calc_2()
                energy_vs_vol.append(
                    [scaled.get_potential_energy(), scaled.get_volume()]
                )

            logger.debug("Sucesfully calculated energy vs vol.")
            return energy_vs_vol

        if self.crystal_struct == "hexagonal" or self.crystal_struct == "tetragonal":
            # Need to scale axis independant of eachoter
            logger.debug(
                f"Start calculating energy vs [a,a,c]\
                         for: {self.crystal_struct}"
            )
            scaling_step = np.linspace(0.95, 1.05, 50)  # increase to get better result

            energy_vs_lat = []

            # Convention that a and b are the same ones.
            for scale_a in scaling_step:
                for scale_c in scaling_step:
                    scaled = conv_atoms.copy()
                    new_cell = (
                        a0 * scale_a,
                        b0 * scale_a,
                        c0 * scale_c,
                        alfa,
                        beta,
                        gamma,
                    )
                    scaled.set_cell(new_cell, scale_atoms=True)
                    scaled.calc = self._check_calc_2()
                    energy_vs_lat.append(
                        [
                            scaled.get_potential_energy(),
                            [a0 * scale_a, b0 * scale_a, c0 * scale_c],
                        ]
                    )

            logger.debug("Sucesfully calculated energy vs [a,a,c]")
            return energy_vs_lat

        if (
            self.crystal_struct == "orthorhomic"
            or self.crystal_struct == "monoclinic"
            or self.crystal_struct == "triclinic"
        ):
            # Need to scale axis independant of eachoter
            # Would require 3-time nested for-loop. For performance assume a,b,c
            # not strongly coupled,
            # and optimize one axis at time
            logger.debug(
                f"Start calculating which [a,b,c]\
                         minimizes: {self.crystal_struct}"
            )
            scaling_step = np.linspace(0.95, 1.05, 50)  # Increase to get better result

            energy_vs_lat = []

            # Start by keeping b and c fixed
            for scale_a in scaling_step:
                scaled = conv_atoms.copy()
                new_cell = (a0 * scale_a, b0 * 1, c0 * 1, alfa, beta, gamma)
                scaled.set_cell(new_cell, scale_atoms=True)
                scaled.calc = self._check_calc_2()
                energy_vs_lat.append([scaled.get_potential_energy(), scale_a])
            logger.debug("Sucesfully found min a")

            # Find lowest a, keep that and c fixed. Vary b
            _, min_a = min(energy_vs_lat, key=lambda x: x[0])
            energy_vs_lat = []
            for scale_b in scaling_step:
                scaled = conv_atoms.copy()
                new_cell = (a0 * min_a, b0 * scale_b, c0, alfa, beta, gamma)
                scaled.set_cell(new_cell, scale_atoms=True)
                scaled.calc = self._check_calc_2()
                energy_vs_lat.append([scaled.get_potential_energy(), scale_b])
            logger.debug("Sucesfully found min b")

            # With lowest a and b, vary c
            _, min_b = min(energy_vs_lat, key=lambda x: x[0])
            energy_vs_lat = []
            for scale_c in scaling_step:
                scaled = conv_atoms.copy()
                new_cell = (a0 * min_a, b0 * min_b, c0 * scale_c, alfa, beta, gamma)
                scaled.set_cell(new_cell, scale_atoms=True)
                scaled.calc = self._check_calc_2()
                energy_vs_lat.append([scaled.get_potential_energy(), scale_c])
            logger.debug("Sucesfully found min c")

            # Return the lowest a,b and c
            _, min_c = min(energy_vs_lat, key=lambda x: x[0])
            return [min_a * a0, min_b * b0, min_c * c0]

    def calc_lattice(self):
        """Determine the equilibrium lattice constants for the conventional cell.

        This method calls :py:meth:`_estimate_lattice` to get energy-vs-lattice data
        and then fits this data to find the lattice parameters that minimize
        the potential energy. The fitting method depends on the crystal
        structure:

        - For cubic or trigonal structures, it performs an Equation of State
          (EOS) fit.
        - For hexagonal or tetragonal structures, it performs a 2D quadratic
          fit to the energy surface.
        - For orthorhombic, monoclinic, or triclinic structures, it returns
          the constants found by the sequential optimization in
          :py:meth:`_estimate_lattice`.

        Returns
        -------
        tuple
            A tuple containing:

            - cov_structure (str): The name of the crystal structure type.
            - list: The optimal lattice constants `[a, b, c]` in Angstroms.
        """
        logger.debug("Start calculating/extracting which optimal lattice const is.")

        energy_v_lattice = self._estimate_lattice()  # Will update self.crystal_struct
        cov_structure = self.crystal_struct

        if not self.crystal_conv:
            logger.debug("No conventional crystal found in resultMD object")
            raise RuntimeError(
                "Cant calc lattice, as no conventional cell\
                               was given when"
                "resultMD object was created"
            )

        logger.debug("Succsesfully called _estimate_lattice()")
        if cov_structure == "cubic" or cov_structure == "triagonal":
            # Do EOS-fit
            logger.debug("Do EOS-fit")
            energies = np.array([e1 for e1, e2 in energy_v_lattice])
            volumes = np.array([e2 for e1, e2 in energy_v_lattice])

            sort_indx = np.argsort(volumes)
            volumes = volumes[sort_indx]
            energies = energies[sort_indx]

            eos = EquationOfState(volumes, energies, eos="birchmurnaghan")
            v0, e0, B = eos.fit()
            logger.debug("Suscsesfully did EOS-fit")
            return cov_structure, [v0 ** (1 / 3), v0 ** (1 / 3), v0 ** (1 / 3)]

        if cov_structure == "hexagonal" or cov_structure == "tetragonal":
            # Since 2 independent axis, need to do a line-fit
            logger.debug("Do quadratic fit")
            energies = np.array([e1 for e1, e2 in energy_v_lattice])
            lattice_consts = np.array([e2 for e1, e2 in energy_v_lattice])

            latt_a = lattice_consts[:, 0]
            latt_c = lattice_consts[:, 2]

            funcs = np.array(
                [latt_a**0, latt_a, latt_c, latt_a**2, latt_a * latt_c, latt_c**2]
            )
            p = np.linalg.lstsq(funcs.T, energies, rcond=-1)[0]

            p1 = p[1:3]
            p2 = np.array([(2 * p[3], p[4]), (p[4], 2 * p[5])])
            a0, c0 = np.linalg.solve(p2.T, -p1)
            logger.debug("Sucssesfully did quadratic fit")
            return cov_structure, [a0, a0, c0]

        # If none of the above, it had 3 independent lattice constants, which we
        # minimized/optimized already.
        logger.debug(
            "Crystal had 3 independent axis. Return the\
                     optimal lattice consts"
        )
        return cov_structure, energy_v_lattice
