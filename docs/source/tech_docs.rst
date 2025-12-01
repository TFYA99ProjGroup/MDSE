==============================
Technical Documentation
==============================

Introduction
============

<This is an introduction! Some text...>


Background
==========

<Short info about underlying concepts and the most important packages/programs being used>

Now follows a short description of underlying libraries, concepts and platforms used by the MDSE software. For more information about external libraries and platforms, see their own respective documentation.

ASE
---

The MDSE software makes great use of the **Atomic Simulation Environment (ASE)** python library. It is a framework for constructing and managing atomic-scale simulations. MDSE uses ASE mainly for its Atoms object which represents atomic positions, relevant properties and corresponding metadata. In addition, ASE's Calculator interface provides a way to attach interatomic potentials to the Atoms object allowing MDSE to integrate different potential models, ensuring a simple but flexible simulation workflow.


ASAP
----
The **Atomistic Simulation Algorithms Package (ASE)** is a python library that works as an extension of ASE. It offers efficient force evaluations, more optimized performance of some potentials as compared to ASE, aswell as support parallelization. ASAP is well suited for large systems where pure ASE is too slow. In MDSE, ASAP is used to accelerate the simulation workflow with optimized calculators and parallellization, thus minimizing core time on the supercomputer.

<
httk

mongoDB

docker?

sqlite, or Joels DB info

Parallellization

Super computer
>


System Overview
===============

MDSE is divided into three major modules, each managing their own large task. This limits which parts of the code can communicate, makes the software less cluttered and makes it easier to expand upon in the future.

.. image:: _static/MD-Design.png
    :alt: Design overview of the product modules. MDSE, *Molecular Dynamics Simulation Environment*.


The simulation module is the main component of MDSE. Running on the ASE and ASAP libraries this module will setup, plan and execute all simulations...

The Data Processing Module...

The Data Visualization Module...


Other header (find a good name)?!?
==================================

<Something to describe systems on a lower level, like every module and how all of their main functions/goals are completed>
