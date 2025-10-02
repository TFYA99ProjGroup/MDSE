from ase.io import Trajectory
import numpy
from ase import units
from MSD import calc_MSD

def calc_self_diff(filename, frames_in_fs = 50):
    """
    Generates MSD(tau) in all directions. Plots it vs tau and fits a linje. The slope is related to self-diffusion
    
    Args:
        frames_in_fs (int): How many fs each frame corresponds to. Example:
                                dyn = VelocityVerlet(atoms, 5 * units.fs)  # 5 fs time step.
                                dyn.attach(traj.write, interval=10)
                                This gives frames_in_fs = 5*10 = 50 fs

    Returns:
        D_total (float): The total self-diffusion w.r.t all dimensions
    """

    #Start by calculating MSD
    taus_fs, MSD_at_tau_x, MSD_at_tau_y, MSD_at_tau_z = calc_MSD(filename, frames_in_fs)

    #Now need to plot MDS(tau) vs tau, slope is here related to D
    from scipy.stats import linregress
    D_slope_x = linregress(taus_fs,MSD_at_tau_x)
    D_slope_y = linregress(taus_fs,MSD_at_tau_y)
    D_slope_z = linregress(taus_fs,MSD_at_tau_z)

    #Calc D in each dimension
    Dx = D_slope_x.slope/(2)
    Dy = D_slope_y.slope/(2)
    Dz = D_slope_z.slope/(2)

    #Calc total D
    D_total = (D_slope_x.slope/(2)+D_slope_y.slope/(2)+D_slope_z.slope/(2))/3

    return D_total

def run_calc():
    my_D = calc_self_diff("test.traj",50)   #10 timesteps, 5fs each
    print("My calculated D")
    print(my_D)


    #Compare to built in slow function
    from ase.md.analysis import DiffusionCoefficient
    my_traj = Trajectory("test.traj")
    dc = DiffusionCoefficient(my_traj,timestep=50)
    D_ase = dc.slopes[0]
    print("D according to ASE")
    print(numpy.mean(D_ase))

 


if __name__ == "__main__":
    run_calc()