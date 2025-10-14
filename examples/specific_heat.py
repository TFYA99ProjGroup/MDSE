from ase.io import Trajectory
import numpy as np
from ase import units

def calc_enthalpy(data):
    #Const
    eV_to_J = 1.602176634e-19
    A3_to_m3 = 1e-30
    au_to_Pa = 1.602176634e11
    u_to_kg = 1.66053906660e-27
    kB = 1.380649e-23

    traj = Trajectory(data)
    E_eV, V_A3, T_K = [], [], [] # ev electronvolt, A3 Angstrom3

    atoms0 = traj[0]
    p_au = atoms0.info['p_au']
    print(atoms0.info.keys())

    m_u = atoms0.get_masses()
    tot_mass_u = m_u.sum()
    tot_mass_kg = tot_mass_u * u_to_kg
    


    p_Pa = p_au * au_to_Pa

    for frame in traj:
        E_eV.append(frame.get_total_energy())
        V_A3.append(frame.get_volume())
        T_K.append(frame.get_temperature())


    traj.close()

    E_J = np.array(E_eV) * eV_to_J
    V_m3 = np.array(V_A3) * A3_to_m3
    T_K = np.mean(T_K)


    # Enthalpy
    H_J = E_J + p_Pa * V_m3
    print('E: ', E_J)
    print('p: ', p_Pa)
    print('V: ', V_m3)
    print('H: ', H_J)


    # Skip equilibration frames
    frame_skips = 0.5
    nskip = int(len(H_J) * frame_skips)
    H_J = H_J[nskip:]

    varH = np.var(H_J)
    Cp = varH / (kB * T_K**2)

    print('Cp: ', Cp)

    specific_heat = Cp / tot_mass_kg
    print("mass_u: ", tot_mass_u)
    print(f"Specific heat capacity: {specific_heat} J/(kg·K)")
    

if __name__ == "__main__":
    calc_enthalpy("test.traj")
