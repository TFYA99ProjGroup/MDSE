from matplotlib.pyplot import axis
import numpy as np
from asap3 import Trajectory, units


class ResultMD:
    """Class representing the result of a molecular dynamics (MD) simulation.

    This class stores frames from a simulation and provides methods to
    calculate and visualize the mean squared displacement (MSD).
    """

    "default constructor, used for list of atoms objects ..."

    def __init__(self, data):
        """Initialize the ResultMD object.

        Args:
            data (list): List of ASE Atoms objects representing simulation frames.
        """
        self.frames = data

    @classmethod
    def from_file(cls, filepath):
        """Create a ResultMD object from a trajectory file.

        Args:
            filepath (str): Path to the trajectory file.

        Returns:
            ResultMD: An instance of the class containing trajectory frames.
        """
        traj = Trajectory(filepath)
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
        positions = np.array([frame.positions for frame in self.frames])
        # positions[t] gives positions ALL atoms at time t
        # positions[t][i] gives position of atom i, at time t
        # positions[t][i][0] gives position of atom i in x-direction, at time t

        taus = range(7, len(self.frames) - 7)

        MSD_at_tau_x = []
        MSD_at_tau_y = []
        MSD_at_tau_z = []

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
        taus_fs = [tau * 10 for tau in taus]

        return taus_fs, MSD_at_tau_x, MSD_at_tau_y, MSD_at_tau_z

    def calc_msd(self):
        """Compute the overall mean squared displacement (MSD).

        Returns:
            float: The average MSD value across all directions.
        """
        _, MSD_x, MSD_y, MSD_z = self._calc_msd_list()
        return np.mean(MSD_x + MSD_y + MSD_z)

    def visualize_msd(self):
        """Visualize the mean squared displacement (MSD) as a function of time lag."""
        import matplotlib.pyplot as plt

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

    def calc_debye_temperature(self):
        frames = self.frames[1:]
        nframes, natoms = np.shape(frames)
        timestep = 2 * units.fs

        velocities = [a.get_velocities() for a in frames]

        velocities = np.array(velocities)

        velocities.reshape(nframes, -1)

        mean_velocities = velocities.mean(axis=0)

        centered_velocities = velocities - mean_velocities

        fft_velocities = np.fft.fft(centered_velocities, axis=0)
        vacf = np.fft.ifft(np.abs(fft_velocities)**2, axis=0).real
        print(vacf.shape)
        vacf = vacf.mean(axis=1)
        vacf /= vacf[0]
        print(vacf.shape)

        freqs = np.fft.fftfreq(nframes, timestep)
        vdos = np.abs(np.fft.fft(vacf))
        mask = freqs > 0
        freqs = freqs[mask]
        vdos = vdos[mask]

        de = freqs[1] - freqs[0]
        g_norm = vdos / np.trapz(vdos, freqs) * (3 * natoms)

        cum_int = np.cumsum(g_norm) * de
        target = 3 * natoms

        idx = np.searchsorted(cum_int, target)

        if idx == 0:
            w_D = freqs[0]
        else:
            f1, f2 = freqs[idx-1], freqs[idx]
            c1, c2 = cum_int[idx-1], cum_int[idx]
            w_D = f1 + (target - c1) * (f2 - f1) / (c2 - c1)

        hbar = 6.582119569e-16
        kB = 8.617333262e-5

        omega_D = 2 * np.pi * w_D * 1e15
        Theta_D = (hbar * omega_D) / kB

        print(f"Debye angular frequency ω_D = {omega_D:.3e} rad/s")
        print(f"Debye temperature Θ_D ≈ {Theta_D:.1f} K")

