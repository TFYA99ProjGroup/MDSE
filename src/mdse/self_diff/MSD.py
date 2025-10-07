from ase.io import Trajectory
import numpy
from ase import units

def calc_MSD(data,frames_in_fs = 50, to_plot = False):
    """
    if data is filepath:
    Reads .traj file and calculates the mean-square-displacement
    if data is array of positions, calculates MSD on that.

    MSD = 1/N*|ri(t+tau)-ri(t+tau)|^2
    For each tau/lag/deltat it looks at all frames saved, for all molecules.

    Parameters:
        filename (str): Name of .traj file
        frames_in_fs (int): How many fs each frame corresponds to. Example:
                                dyn = VelocityVerlet(atoms, 5 * units.fs)  # 5 fs time step.
                                dyn.attach(traj.write, interval=10)
                                This gives frames_in_fs = 5*10 = 50 fs

    Returns:
        taus_fs: A list containing all the taus that MSD was calculated for. (In fs units not frames)
        MSD_at_tau_x: List containing MSD(tau) in x direction
        MSD_at_tau_y: List containing MSD(tau) in x direction
        MSD_at_tau_z: List containing MSD(tau) in x direction


    TODO: Use vectors in numpy instead for nested for-loops
          !!Unwrap positions because of PBC!!
    """

    if isinstance(data,str): #A filepath
        my_traj = Trajectory(data)

        #Number of frames saved
        frames = len(my_traj)
        #Start by extracting all positions
        positions = []
        for frame in my_traj:
            positions.append(frame.positions) #Gives ALL atoms in a frame
        #positions[t] gives positions ALL atoms at time t
        #positions[t][i] gives position of atom i, at time t
        #positions[t][i][0] gives position of atom i in x-direction, at time t

        #Convert to numpy array
        positions = numpy.array(positions)

        
        #MSD has alot of noice in beggning => choose larger starting point
        #Also noice at the end, so cut-off tau
        tau_start = 1
        tau_end = frames
        #But KEEP noice, can be filtered out later

        #Number of particles
        N = len(my_traj[0])


    elif isinstance(data,numpy.ndarray): #Array with positions
        positions = data
        frames = len(positions)

        #Only used if testing, hence must use low tau
        tau_start = 0
        tau_end = frames

        N = len(positions[0])

    #Number of time-lag (tau) we whant to do
    taus = []
    for a in range(tau_start,tau_end): #Runs faster the fewer taus
        taus.append(a)

    MSD_at_tau_x = []
    MSD_at_tau_y = []
    MSD_at_tau_z = []

    for tau in taus:
        MSD_at_all_t_x = [] #Reset per tau
        MSD_at_all_t_y = [] #Reset per tau
        MSD_at_all_t_z = [] #Reset per tau
        for timestep in range(0,frames-tau): #timestep != frames. Good as starts on 0

            #Calculate |ri(t+tau) - ri(t)|^2 
            displacement_x = positions[timestep,:,0]-positions[timestep+tau,:,0]
            #Array containing displacement on x for ALL atoms, durint t=timestep

            displacement_y = positions[timestep,:,1]-positions[timestep+tau,:,1]
            displacement_z = positions[timestep,:,2]-positions[timestep+tau,:,2]

            #square and average over all atoms
            MSD_x_t = numpy.sum(displacement_x**2)/N
            MSD_y_t = numpy.sum(displacement_y**2)/N
            MSD_z_t = numpy.sum(displacement_z**2)/N
        
            #Move to next time-step
            MSD_at_all_t_x.append(MSD_x_t)
            MSD_at_all_t_y.append(MSD_y_t)
            MSD_at_all_t_z.append(MSD_z_t)

        #Average over the time
        MSD_final_x = sum(MSD_at_all_t_x) / len(MSD_at_all_t_x)
        MSD_final_y = sum(MSD_at_all_t_y) / len(MSD_at_all_t_y)
        MSD_final_z = sum(MSD_at_all_t_z) / len(MSD_at_all_t_z)

        MSD_at_tau_x.append(MSD_final_x)
        MSD_at_tau_y.append(MSD_final_y)
        MSD_at_tau_z.append(MSD_final_z)

    #Remeber: Tau is in frames now. Convert to fs
    taus_fs = [tau * frames_in_fs for tau in taus]

    #------Print MDS(tau) vs tau
    if (to_plot):
        import matplotlib.pyplot as plt

        plt.figure(figsize=(6,4))
        plt.plot(taus_fs, MSD_at_tau_x, label='MSD X', marker='o')
        plt.plot(taus_fs, MSD_at_tau_y, label='MSD Y', marker='s')
        plt.plot(taus_fs, MSD_at_tau_z, label='MSD Z', marker='^')

        plt.xlabel('Time lag τ (fs)')
        plt.ylabel('MSD (?²)')
        plt.title('Mean Squared Displacement vs Time Lag')
        plt.legend()
        plt.grid(True)
        plt.tight_layout()
        plt.show()
    #----------------

    return taus_fs, MSD_at_tau_x, MSD_at_tau_y, MSD_at_tau_z

if __name__ == "__main__":
    #argon needs time_step = 100
    #Cu needs time_step = 50
    calc_MSD("argon.traj",50,True)