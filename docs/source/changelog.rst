==========================
Changelog
==========================

All notable changes to this project are documented here.

Version 1.0.0 (2025-12-12)
===========================

**Added**
----------
- Following calculations can be performed: 
    - Density of states
    - Debye temperature
    - Elastic moduli and constants
        - Shear modulus
        - Bulk modulus
        - Young’s modulus
    - Coheseive energy (in the form of Atomization energy)
    - Formation energy
    - Defect formation energy
- Ability to run simulations from SQLite database
    - Creates .cif files and simulates from them.
- Ability to use a `MACE potential model <https://github.com/ACEsuit/mace>`_ (MLIP)
- Different types of visualization from our MongoDB
- Result database is compliant with `OPTIMADE API <https://www.optimade.org/>`_
- More functions in the CLI 

**Changed**
------------
- Added `httk <ittps://github.com/httk/httk>`_ as a dependency in order to read SQLite db


----

Version 0.2.0 (2025-11-12)
===========================

**Added**
----------
- More robust config-files
- Ability to save simulation results to `MongoDB <https://www.mongodb.com/docs/>`_ database.
- Parallelism for running on a supercomputer.
- Plotting functions


**Changed**
------------
- New format of the config-files.
- New dependency: MPI, e.g. `Open MPI <https://www.open-mpi.org/>`_ in order to run parallel on many cores. 

----


Version 0.1.0 (2025-10-20)
===========================

**Initial public release.**

**Added**
----------
- Simple MD-simulation with NVE and NPT ensambles with ASE, parsed from yaml-config file.
- Simple visualization with ASE.
- Command line interface, CLI.
- Following calculations can be performed: 
    - Mean square displacement (MSD)
    - Lindemann melting criterion
    - Self diffusion coefficient
    - Isobaric specific heat per atom

----

Older Versions
===============

*(No earlier versions.)*

