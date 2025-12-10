==============================
Technical Documentation
==============================

Introduction
============

This documentation describes how MDSE works and the methods used.


Background
==========

This section describes the underlying libraries, concepts and platforms used by the MDSE software.
For more information about external libraries and platforms, see each library's own respective documentation.

ASE
---

The MDSE software makes great use of the **Atomic Simulation Environment (ASE)** python library [#]_.
It is a framework for constructing and managing atomic-scale simulations. MDSE uses ASE mainly for its
Atoms object which represents atomic positions, relevant properties and corresponding metadata. In addition, 
ASE's Calculator interface provides a way to attach interatomic potentials to the Atoms object allowing MDSE to
integrate different potential models, ensuring a simple but flexible simulation workflow.

ASAP
----
The **As Soon As Possible (ASAP)** is a python library that works as an extension of ASE [#]_. It offers
efficient force evaluations, more optimized performance of some potentials as compared to ASE, aswell as support 
parallelization. ASAP is well suited for large systems where pure ASE is too slow. In MDSE, ASAP is used to accelerate
the simulation workflow with optimized calculators and parallelization, thus minimizing core time on the supercomputer.

httk
----

The **High-Throughput Tool Kit (httk)** is a toolkit for preparing and running calculations, analyzing
the results, and storing results in global and/or personalized databases [#]_. MDSE uses the `httk.db` module to 
communicate with an sqlite database containing material defects.

Parallelization
---------------

Parallelization is the concept of letting different cores of the CPU do different computations simultaneously
to optimize efficiency and minimize computation time. MDSE makes use of the **Message Passing Interface (MPI)**
to accomplish this feat.

pymongo
-------

MDSE uses the pymongo python library to read and write to a mongoDB server.

Optimade API
------------

The optimade API is used to make sure that the results of MDSE are compatible with the FAIR-principles of materials data.

Docker
------



System Overview
===============

MDSE is divided into two major modules, each managing their own large task. This limits which parts of
the code can communicate, makes the software less cluttered and makes it easier to expand upon in the future.
An overview of the modules can be seen in the Figure below.

.. image:: _static/MD-Design.png
    :alt: Overview of MDSE modules.


The simulation module is the main component of MDSE. Running mainly on the ASE and ASAP libraries this
module will setup, plan and execute all simulations. It receives a user specified configuration and creates
appropriate simulations based on the input.

The Data Processing Module is responsible for communicating with the database and is used to visualize and process the data.

Simulation Workflow
===================

CLI
---

MDSE is developed to operate via a command line interface. Here the user is able to run all pre
configured MD simulations by specifying a configuration file. This describes what to simulate, 
crystal properties, simulation settings such as temperature, length of simulation,
ensemble, etc. aswell as which properties to calculate. Further information on the format of the configuration file
is specified in :py:mod:`mdse.parser`.
There are also flags implemented which lets the user overwrite properties specified in the configuration file.

Simulations
-----------

Simulations begin by requiring a user specified configuration in a YAML file.
MDSE parses the config file through the :py:mod:`mdse.parser`
module. The parsed information is sent to the run manager which manages the simulations generated from the parser.

The run manager creates multiple :py:class:`~mdse.md.simulationmanager.SimulationManager` objects which contain
the crystal structure to be simulated and the simulation settings, such as temperature, length of simulation,
ensemble, etc. The crystal is an ASE [1]_ ``Atoms`` object and a calculator is attached to it for the specified
potential. Then an MD simulation based on the settings is performed with ASE and ASAP.

Calculations
------------

When a simulation is done the run manager will call upon :py:class:`~mdse.md.resultMD.ResultMD` objects which are created
from the simulation. These objects contain the data related to each frame of a simulation and are used to calculate
material properties of the simulated crystal. When calculating material properties a check for equillibrium is
done to get rid of data that will skew the results. Results are then calculated as time averages over the remaining
frames to find the most accurate values.

Database
--------

MDSE uses two main databases to store material properties. The first one, mongoDB, is
hosted locally via a docker compose file.

<Babbla lite om databaserna och hur de hanteras>


References
==========

.. [#] Atomic Simulation Environment (ASE), https://ase-lib.org/
.. [#] As Soon As Possible (ASAP), https://asap3.readthedocs.io/en/latest/
.. [#] The High-Throughput Toolkit (httk), https://docs.httk.org/en/latest/

