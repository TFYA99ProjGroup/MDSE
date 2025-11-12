from matplotlib import pyplot as pl
from scipy import constants
import numpy as np
from asap3 import Trajectory
from ase import units

import logging

logger = logging.getLogger(__name__)


class ResultMD:
    """Class representing the result of a molecular dynamics (MD) simulation.

    This class stores frames from a simulation and provides methods to
    calculate and visualize the mean squared displacement (MSD).
    """

    "default constructor, used for list of atoms objects ..."

    def __init__(self, data):
        """Initialize the ResultMD object.

        Parameters:
            data (list): List of ASE Atoms objects representing simulation frames.
        """
        logger.debug("Initialize ResultMD")

        self.frames = data
        self.frames_in_fs = 50
        self.name = ""
        self.reached_equilibrium = False

        self.dos = None
        logger.debug("Init done")

    @classmethod
    def from_file(cls, filepath):
        """Create a ResultMD object from a trajectory file.

        Parameters:
            filepath (str): Path to the trajectory file.

        Returns:
            ResultMD: An instance of the class containing trajectory frames.
        """
        logger.debug(f"Creating instances of ResultMD from {filepath}")
        try:
            traj = Trajectory(filepath)
        except Exception as e:
            logger.error(e)
            raise
        return cls([atom for atom in traj])

    def _calc_msd_list(self):
        """Calculate the mean squared displacement (MSD) for each direction.

        Returns:
            tuple: A tuple containing:
                - taus_fs (list): Time lags in femtoseconds.
                - MSD_at_tau_x (list): MSD values in the x-direction.
                - MSD_at_tau_y (list): MSD values in the y-direction.
                - MSD_at_tau_z (list): MSD values in the z-direction.
        """
        logger.debug("Beginning calculations for MSD")
        positions = np.array([frame.positions for frame in self.frames])
        # positions[t] gives positions ALL atoms at time t
        # positions[t][i] gives position of atom i, at time t
        # positions[t][i][0] gives position of atom i in x-direction, at time t

        #Check if equilibrium, filter out bad start
        self.check_equilibrium()
        if self.reached_equilibrium:
            positions = positions[self.check_equilibrium() :]
        #taus = range(7, len(self.frames) - 7)
        taus = range(7, len(positions) - 7)
        #Comment: This removes very short taus. So short timesteps
        #But we still get the early frames. Nothing to-do with equilibrium
        

        MSD_at_tau_x = []
        MSD_at_tau_y = []
        MSD_at_tau_z = []

        logger.debug("Beggining iteration over tau")
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

    def calc_msd(self):
        """Compute the overall mean squared displacement (MSD).

        Returns:
            float: The average MSD value across all directions.
        """
        logger.debug("Begginning calc_msd")
        _, MSD_x, MSD_y, MSD_z = self._calc_msd_list()
        return np.mean(MSD_x + MSD_y + MSD_z)

    def estimate_nearest_neighbor_distance(self, positions):
        """Estimate average nearest-neighbor distance for one frame.

        Args:
            positions (ndarray): shape (N, 3) array of atomic positions.
        Returns:
            float: average nearest-neighbor distance for one frame.
        """
        diffs = positions[:, np.newaxis, :] - positions[np.newaxis, :, :]
        dists = np.sqrt(np.sum(diffs**2, axis=-1))
        np.fill_diagonal(dists, np.inf)
        nearest = np.min(dists, axis=1)
        return np.mean(nearest)

    def estimate_average_a(self):
        """Estimate the average nearest-neighbor distance over all frames.

        Returns:
            float: The average nearest-neighbor distance across all frames.
        """
        all_a = [
            self.estimate_nearest_neighbor_distance(f.positions) for f in self.frames
        ]
        return np.mean(all_a)

    def calc_lindemann(self, a=None):
        """Compute the global Lindemann parameter.

        Args:
            a (float): Average nearest-neighbor distance.
        Returns:
            float: Lindemann parameter `delta_L`.
        """
        logging.debug("Calculate lindemann")
        if a is None:
            a = self.estimate_average_a()
        msd = self.calc_msd()
        return np.sqrt(msd) / a

    def visualize_msd(self):
        """Visualize the mean squared displacement (MSD) as a function of time lag."""
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

        Args:
            frame_skip (float, optional): Fraction of the *total* initial
                frames to skip (e.g., for equilibration). Defaults to 0.5.
            max_lag (float, optional): Fraction of the *remaining* frames
                (after skipping) to use as the maximum lag time. The
                returned VACF will have this many points. Defaults to 0.5.

        Returns:
            numpy.ndarray: A 1D array containing the normalized VACF. Its
                length will be `int((1 - frame_skip) * len(self.frames) * max_lag)`.
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

        Args:
            frame_skip (float, optional): Fraction of the total initial
                frames to skip (e.g., for equilibration). This value is
                passed directly to ``self._calc_vacf`` and is also used
                to select the frames for calculating ``natoms``.
                Defaults to 0.5.

        Returns:
            tuple: A tuple of `(dos, omega)`:
                - **dos** (numpy.ndarray): The 1D array of the normalized
                  density of states.
                - **omega** (numpy.ndarray): The 1D array of the corresponding
                  angular frequencies. The units depend on the units of
                  `dt` (e.g., rad/fs if `dt` is in fs).
        """
        self.check_equilibrium()
        if self.reached_equilibrium:
            max_lag = self.check_equilibrium()
            frame_skip = max_lag/len(self.frames)
        else:
            max_lag = int(frame_skip * len(self.frames))
        frames = self.frames[max_lag:]
        _, natoms = np.shape(frames)
        dt = frames[0].info["dt"] * 1e-15 / units.fs
        logger.debug((
            ("Calculating density of states for system."),
            (f"frames: {max_lag}, natoms: {natoms}, dt: {dt} fs")),
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
        """Visualize the density of states as a function of angular frequency."""
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

        1. Calls ``self.calc_density_of_states(frame_skip)`` to get the `dos` \
            and angular frequency `omega` arrays.
        2. Calculates the cumulative integral of the DOS with respect to \
            `omega` (i.e., the total number of modes up to a given frequency).
        3. Finds the index where this cumulative integral first matches or \
            exceeds the target degrees of freedom (3N).
        4. The frequency at this index is taken as the Debye frequency.
        5. Converts the Debye frequency to the Debye temperature using the \
            relation
            .. math::
                \\Theta_D = \\frac{\\hbar \\omega_D}{k_B}.

        Args:
            frame_skip (float, optional): Fraction of the total initial \
                frames to skip (e.g., for equilibration). This value is \
                passed directly to `self.calc_density_of_states`. \
                Defaults to 0.5.

        Returns:
            float: The calculated Debye temperature ``Theta_D``. The units \
                (e.g., Kelvin) depend on the `dt` value from the frames.
        """
        kB = constants.Boltzmann
        hbar = constants.hbar
        _, natoms = np.shape(self.frames)

        self.check_equilibrium()
        if self.reached_equilibrium:
            frame_skip = self.check_equilibrium() / len(self.frames)

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
        """Calculates self diffusion coefficient using MSD.
        Requires a linear-fit, so filters out noisy tau values. (Might need fine-tuning)

        Returns:
            D_total (float): Self diffusion coefficent, w.r.t all directions.
        """
        taus_fs, MSD_of_tau_x, MSD_of_tau_y, MSD_of_tau_z = self._calc_msd_list()

        # Filter out noisy start/end, 10%
        """
        if self.reached_equilibrium:
            filter_start = self.check_equilibrium()
        else:
            filter_start = int(len(MSD_of_tau_x) * 0.1)"""
        filter_start = 0 #should already have filtered out first bad frames in calc_msd
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

        Returns:
            enthalpy_J (float): Enthalpy with unit Joule.

        Note:
            Developers, you need a calc to get the total energy. Btw,
            if you just began reading theese docs, calc stands for calculator.
        """
        E_eV, V_A3 = [], []

        p_au = self.frames[0].info["p_au"]

        p_Pa = p_au * (constants.eV / (constants.angstrom**3))

        logger.debug(f"au_to_Pa: {constants.eV / (constants.angstrom**3)}")
        for frame in self.frames:
            E_eV.append(frame.get_total_energy())
            V_A3.append(frame.get_volume())

        E_J = np.array(E_eV) * constants.eV
        V_m3 = np.array(V_A3) * (constants.angstrom**3)

        logger.debug(f"ev_to_J: {constants.eV}")
        logger.debug(f"angstrom: {constants.angstrom}")

        enthalpy_J = E_J + p_Pa * V_m3
        logger.debug(f"enthalpy {enthalpy_J}")
        return enthalpy_J

    def calc_isobaric_specific_heat(self):
        """Caluclates isobaric specific heat or c_p after a NPT ensemble.

        Returns:
            specific heat (float): Specific heat in units J / (kg * K).
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
        """Calculates the heat capacity per atom after a NVT ensemble.

        Returns:
            Heat capacity per atom (float): Heat capacity per atom in units J / (n * K)
        """
        E_eV, T_K = [], []

        for frame in self.frames:
            E_eV.append(frame.get_total_energy())
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

    def get_pot_energies(self):
        """Gets the potential energis at each frame.

        returns:
            list: Potential energy at each frame
        """
        logger.debug("Get potential energies")
        return [frame.get_potential_energy() for frame in self.frames]

    def get_kin_energies(self):
        """Gets the kinnetic energis at each frame.

        returns:
            list: Kinnetic energy at each frame
        """
        logger.debug("Get kinetic energies")
        return [frame.get_kinetic_energy() for frame in self.frames]
    
    def get_tot_energies(self):
        """Gets total energy at each frame
        
        returns:
            list: Total energy at each frame
        """
        logger.debug("Get total energies")
        return[frame.get_kinetic_energy() + frame.get_potential_energy() for frame in self.frames]

    def get_time_axis(self):
        """Gets the time steps where frames are from.

        returns:
            times (list): Contains at what times each frame is from.
        """
        logger.debug("Get an time-axis")
        dt = self.frames[0].info["dt"]
        times = np.arange(len(self.frames)) * dt
        return times
    
    def get_temperatures(self):
        """Gets temperature for all frames

        returns:
            list: List of all temperatures at each frame
        """
        logger.debug("Get tempertures")
        return [frame.get_temperature() for frame in self.frames]
    
    def check_equilibrium(self):
        """Checks whetever the simulation reached equilibrium.
        Also sets at what frame this happens
        
        returns:
            pos (int): Index of where equilibrium was found. 0 if no equilibrium found.
        """
        logger.debug("Started check if equilibrium was reached")
        kin_energy = self.get_kin_energies()
        pot_energy = self.get_pot_energies()
        Tot_energy = [kin+pot for (kin, pot) in zip(kin_energy, pot_energy)]
        temperatures = self.get_temperatures()

        #Too short to check equilibrium
        if (len(self.get_kin_energies()) < 10):
            self.reached_equilibrium = False
            logger.debug("Simulation had too few frames. No equilibrium")
            return 0
         #----Based on total energy-----

        energy_frame = self._check_equilibrium_const(Tot_energy,0.0001)

        if energy_frame != len(Tot_energy)-2: #We found equilibrium
            self.reached_equilibrium = True
            logger.debug("Found equilibrium, energy reaches const value")
            return energy_frame

         #----Based on temperature-----

        temp_frame = self._check_equilibrium_const(temperatures,0.001)
        
        if temp_frame != len(temperatures)-2: #We found equilibrium
            self.reached_equilibrium = True
            logger.debug("Found equilibrium, temperature reaches const value")
            return temp_frame
        
        #----If oscillating system----

        oscill_frame = self._check_equilibrium_oscill(Tot_energy, 0.005)
        if oscill_frame != len(Tot_energy)-2: #We found equilibrium
            self.reached_equilibrium = True
            logger.debug("Found equilibrium, energy oscillates")
            return oscill_frame
        
        #----No equilibrium---
        self.reached_equilibrium = False
        logger.debug("No equilibrium was found")
        return 0
        

    def _check_equilibrium_const(self, property,tol):
        """Checks when a propery starts to stabalize around a constant value.
        
        args:
            Property (list): List containing property for all frames
            tol (float): Tolerance of when energy has reached constant value
        returns:
            pos (int): Position of frame where equilibrium starts
        """
        logger.debug("Check if we have equilibrium in the form of constant energy")
        difference = [abs(property[i+1]-property[i])/property[i] for i in range(len(property)-1)]
 
        for pos,diff in enumerate(difference):
            if (diff <= tol):
                break
            else:
                pass

        return pos

    def _check_equilibrium_oscill(self, Tot_energy, tol):
        """Checks if energy follows an oscillating pattern. Look at a window, do a mean.
        Then move the window along the frames and see how mean changes. When stops changing much,
        we are over an oscillating area.

        args:
            Tot_energy (list): List of total energy for all frames
            tol (float): The tolerance in % from total mean value
        returns:
            pos (int): At what frame we start getting within tolerance
        """
        logger.debug("Check if equilibrium, in oscillating behavior")
        window_lenght = 5
        windows = [Tot_energy[i: (i+window_lenght)] for i in range(0,len(Tot_energy)-window_lenght)]
        #Mean of each window
        windows_means = np.array([sum(win)/len(win) for win in windows])


        diffs = [abs(windows_means[i+1]-windows_means[i]) / windows_means[i] for i in range(len(windows_means)-1)]
        #Find where we start oscillating
        if len(diffs) == 0:
            pos = len(Tot_energy)-2

        for pos, diff in enumerate(diffs):
            if( diff < tol):
                return pos
            else:
                pass

        return len(Tot_energy)-2
