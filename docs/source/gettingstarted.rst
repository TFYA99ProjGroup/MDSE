==============================
User's Manual
==============================

Introduction
============

Welcome to **Molecular Dynamics Simulation Environment (MDSE)**!  
This software parses, runs and evaluates `ASE <https://ase-lib.org/>`_  simulations with the help of `ASAP3 <https://asap3.readthedocs.io/en/latest/>`_. 

This software is developed towards solving problems regarding defect materials using existing data from a database at
Linköping University, parsed via `The High-Throughput Toolkit (httk) <https://github.com/httk/httk>`_.
It is used to explore the possibility of running MD simulations with the help of MLIPs such as the 
`MACE <https://github.com/ACEsuit/mace>`_ calculator instead of 
density functional theory (DFT) to calculate the defect formation energy. This was interesting because
DFT calcuations are heavy and takes a lot of time and so doing it with MACE could be a lot faster. 
The question investigated was whether MACE is accurate enough.

Physical properties:
====================

The following material properties can be calculated with mdse:

- Mean square displacement
- Lindemann index
- Density of states
- Debye temperature
- Self diffusion coefficient
- Isobaric specific heat
- Isochoric heat capacity per atom
- Elastic moduli and constants
    - Shear modulus
    - Bulk modulus
    - Young's modulus
- Coheseive energy (in the form of Atomization energy)
- Formation energy
- Defect formation energy
Installation
============

Requirements
------------

Dependencies:
    - Python >=3.9.21, <3.12

Optional (Highly recommended):
    - Message Passing Interface (MPI), e.g. `Open MPI <https://www.open-mpi.org/>`_ 


Installation from source
------------------------

Using a `conda <https://anaconda.org/anaconda/conda>`_ environment is highly recommended:

.. code-block:: bash

    conda create -n mdseenv python=3
    conda activate mdseenv


.. code-block:: bash

   git clone https://github.com/TFYA99ProjGroup/MDSE
   cd MDSE
   pip install -e .


Quick Start
===========

Run your first simulation:

.. code-block:: bash

    mdse simulate --filepath examples/test_result_sim.yaml

If you want to see the ASE GUI for the trajectory:

.. code-block:: bash

    mdse view

If you want to clean up your directory from ``*.traj`` files:

.. code-block:: bash

    mdse clean

Some interesting results are saved in the /results folder in ``*.json`` files. 


Set up your own server
======================

This program is able to save the result data to a `MongoDB server <https://www.mongodb.com/>`_.
In order to Set up the server docker is highly recommended and a docker-compose file is available in the project:

.. code-block:: bash

    cd database
    docker compose up -d
    cd ..

In order to shut down the database:

.. code-block:: bash

    cd database
    docker compose down

Write your first simulation results to the database!

.. code-block:: bash

    mdse write_db -f results/ -a mongodb://admin:secret@localhost:27017/

You can view the database in a web browser on the address http://localhost:8081/
with the default username *webadmin* and the default password *websecret*.


CLI Usage
=========================

Basic usage
-----------

.. code-block:: bash

   mdse --help

Commands
--------

.. list-table::
   :header-rows: 1

   * - Commands
     - Description
   * - ::
        
        mdse [-h] [--debug] {subcommand} ...
     - The main CLI command


.. list-table::
   :header-rows: 1
   :widths: 35 65

   * - Command
     - Description
   * - ::
     
         simulate [-h] -f FILEPATH [-e ENSAMBLE] [--mpi]
     - Runs the main simulation from config-file.

   * - ::

         view [-h] [-f FILEPATH [FILEPATH ...]]

     - Triggers the ASE GUI from traj-files.

   * - ::

         clean [-h] [-f FILEPATH] [-r]
     - Removes all the traj-files.

   * - ::

         write_db [-h] -f FILEPATH [FILEPATH ...] -a ADDRESS

     - Writes data from json-file to MongoDB database.

   * - ::

         visualize [-h] -f FILEPATH

     - Visualizes data from database. Uses config file too.

   * - ::

         calc_defect_formation_energy [-h] -a ADDRESS

     - Calculates the defect formation energy from a database.

   * - ::

         outliers [-h] -a ADDRESS [-p PROPERTY [PROPERTY ...]] [--db-client DB_CLIENT] [--db-collection DB_COLLECTION] [--std-dev STD_DEV_THRESHOLD]

     - Detects outliers in the database.

Library Usage
=============================

MDSE can also be used as a Python library:

.. code-block:: python

   import mdse

Example
-------

.. code-block:: python
   
   from mdse.parser.parse_yml import main_read
   from mdse.rm.runmanager import RunManager
   from mdse.rm.dbmanager import DBManager
   
   # Parse the yaml-file from your first simulation
   sim_list = main_read("examples/test_result_sim.yaml")

   # Simulate your first simulation again
   rm = RunManager(sim_list)
   rm.run_simulations()

   # Write the data to the database
   dbm = DBManager("mongodb://admin:secret@localhost:27017/")
   dbm.write_jsonfiles_to_db("results")

Workflows
=========

Description of recommended workflows or common tasks.

1. Write config files or a directory with config files (the parser takes both).
2. Run simulation, this software is made to be run on a supercomputer, so that is recommended.
3. Write results to the database.
4. Evaluate the results locally.

Troubleshooting
===============

Common Issues
-------------

.. admonition:: Problem: NPT simulation doesn't work

   **Solution:** Ensure your config contains:

   - Temp
   - Pressure
   - ThermoTime
   - BaroTime

Logging / Debug Mode
--------------------

Add the `--debug` flag to after the mdse cli command:

.. code-block:: bash

    mdse --debug simulate ...

If using MDSE as a library:

.. code-block:: python
   
   from mdse.parser.parse_yml import main_read
   from mdse.rm.runmanager import RunManager
   from mdse.rm.dbmanager import DBManager

   from mdse.logging.logging_config import setup_logging
   import logging
   
   logger = logging.getLogger(__name__)
   # Use debug=False if you want less information
   setup_logging(debug=True)

   # ...

FAQ
===

Q: What does calc stand for?  
A: Calc is slang for calculator.



Version Compatibility
=====================

This software is based around working with Python 3.10 (3.10.12 to be precise)

Changelog
=========

Full changelog is available in :doc:`changelog`.

License
=======

Full license is available in :doc:`license`

Credits:
========

This program used the high-throughput toolkit
  httk v1.2.0 (2020-09-25), (c) 2012 - 2020

Credits for httk modules used in this run:
  - (httk) Rickard Armiento
  - (imported spacegroup data) Computational Crystallography Toolbox, http://cctbx.sourceforge.net/
  - (imported code from cif2cell) Torbjörn Björkman
  - (httk_db) Rickard Armiento

Credits for MDSE:
  - Emil Alakulju  
  - Oskar Bollner  
  - Petter Johansson  
  - Axel Kemppe  
  - Patrik Modorato  
  - Lukas Smith

Contact / Support
=================

It is possible to open an issue in GitHub: `<https://github.com/TFYA99ProjGroup/MDSE/issues>`_. 

Note however that this software will not be supported continually after the 16th January 2026.  

Until then, you can contact our Product owner:
    - oskbo133@student.liu.se
    - H305b, Hertz, F-house, Linköping University


