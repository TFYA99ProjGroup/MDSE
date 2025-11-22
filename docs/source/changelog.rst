==========================
Changelog
==========================

All notable changes to this project are documented here.

Version 0.2.0 (2025-11-12)
===========================

**Added**
----------
- More robust config-files
- Ability to save simulation results to `MongoDB <https://www.mongodb.com/docs/>`_ database.
- Parallelisme for running on a supercomputer.
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

