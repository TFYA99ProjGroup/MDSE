==============================
Technical Documentation
==============================

Introduction
============

<This is an introduction! Some text...>


Background
==========

<Short info about underlying concepts and the most important packages/programs being used>

Now follows a short description of underlying libraries, concepts and platforms used by the MDSE software. For more information about external libraries and platforms, see each libraries own respective documentation.

ASE
---

The MDSE software makes great use of the **Atomic Simulation Environment (ASE)** python library [#]_. It is a framework for constructing and managing atomic-scale simulations. MDSE uses ASE mainly for its Atoms object which represents atomic positions, relevant properties and corresponding metadata. In addition, ASE's Calculator interface provides a way to attach interatomic potentials to the Atoms object allowing MDSE to integrate different potential models, ensuring a simple but flexible simulation workflow.

ASAP
----
The **As Soon As Possible (ASAP)** is a python library that works as an extension of ASE [#]_. It offers efficient force evaluations, more optimized performance of some potentials as compared to ASE, aswell as support parallelization. ASAP is well suited for large systems where pure ASE is too slow. In MDSE, ASAP is used to accelerate the simulation workflow with optimized calculators and parallelization, thus minimizing core time on the supercomputer.

httk
----

The **High-Throughput Tool Kit (httk)** is a toolkit for preparing and running calculations, analyzing the results, and storing results in global and/or personalized databases [#]_. MDSE uses this toolkit to be able to communicate with and initialize simulations from an sqlite database containing material defects.

Parallelization
---------------

Parallelization is the concept of letting different cores of the CPU do different computations simultaneously to optimize efficiency and minimize computation time. MDSE makes use of the **Message Passing Interface (MPI)** to accomplish this feat. MPI is

mongoDB

<
docker?

sqlite, or Joels DB info


Super computer
>


System Overview
===============

<This whole section should be discussed to find a up to date model of our program>

MDSE is divided into three major modules, each managing their own large task. This limits which parts of the code can communicate, makes the software less cluttered and makes it easier to expand upon in the future.

.. image:: _static/MD-Design.png
    :alt: I think it's time to remake this...


The simulation module is the main component of MDSE. Running mainly on the ASE and ASAP libraries this module will setup, plan and execute all simulations. It receives a user specified configuration and creates an appropriate simulation based on the input.

Result Module?

The Data Processing Module...

The Data Visualization Module...


Simulation Workflow
===================

<Should describe the workings of all major parts of MDSE. Aimed to be like a narrative and not like simply reading through the code.

Simulations
-----------
Simulations begin by requiring a user specified configuration in a YAML file and optionally a CIF file. This describes exactly what the simulation will do, molecular properties, desired ensemble, simulation properties aswell as which properties to calculate. An MDSE parser reads the config and passes the information to a run manager which manages multiple simultaneous simulations aswell as parallelization.

The run manager creates an instance of the ASE [1]_ Atoms object and attaches a calculator for the specified potential. Then an MD simulation based on the configuration is performed with ASE or ASAP and all frames before equillibration are removed to improve the accuracy of calculations.

Calculations
------------

When a simulation is done and the crystal structure is relaxed the run manager will begin calculating all material properties specified by the user. The run manager first checks for equillibrium and removes all previous frames as these are not useful for calculating any material properties. Results are then calculated as time averages over the remaining equillibration frames to find the most accurate values.

Database
--------

MDSE uses two main databases to store material properties. The first one, mongoDB, is hosted locally via a docker compose file.

<Babbla lite om databaserna och hur de hanteras>

CLI
---

MDSE is developed to operate via the command line interface. Here the user is able to run all pre configured MD simulations by specifying a configuration file. There are also terminal flags implemented which lets the user <?overwrite?> properties specified in the configuration file.


References
==========

.. [#] Atomic Simulation Environment (ASE), https://ase-lib.org/
.. [#] As Soon As Possible (ASAP), https://asap3.readthedocs.io/en/latest/
.. [#] The High-Throughput Toolkit (httk), https://docs.httk.org/en/latest/

