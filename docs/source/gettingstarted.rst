==============================
User's Manual
==============================

Introduction
============

Welcome to **Molecular Dynamics Simulation Environment (MDSE)**!  
This software parses, runs and evaluates `ASE <https://ase-lib.org/>`_  simulations with help of `ASAP3 <https://asap3.readthedocs.io/en/latest/>`_. 

This software is specified to solve problems regarding defect materials using excisting database from
Linköping University, parsed via. `The High-Throughput Toolkit (httk) <https://github.com/httk/httk>`_.
It was used to explore the possibility to use the `MACE <https://github.com/ACEsuit/mace>`_ instead of 
density functional theory (DFT) to calculate the defect formation energy. This was interesting because
DFT calcuation are heavy and takes a lot of time and so doing it with MACE could be a lot faster. Is 
MACE accurate is the question which was researched using this software.

Features
========

- Feature 1
- Feature 2
- Feature 3

Installation
============

Requirements
------------

List system requirements, Python version, optional dependencies, etc.

Example:
    - Python 3.10+
    - NumPy, SciPy

Installation via pip

    Feature 1

    Feature 2

    Feature 3

--------------------

.. code-block:: bash

   pip install projectname

Installation from source
------------------------

.. code-block:: bash

   git clone https://github.com/username/projectname.git
   cd projectname
   pip install -e .

Configuration
=============

Explain any configuration files, environment variables, or settings.

Example:
    The configuration file is located at ``~/.projectname/config.yaml``.

    Example config:

    .. code-block:: yaml

       option1: true
       path: /data/project

Quick Start
===========

Give the shortest possible example showing how to use the library.

.. code-block:: python

   from projectname import Project

   p = Project()
   p.run()

CLI Usage (if applicable)
=========================

Basic usage
-----------

.. code-block:: bash

   projectname --help

Commands
--------

.. list-table::
   :header-rows: 1

   * - Command
     - Description
   * - ``run``
     - Runs the main program
   * - ``config``
     - Prints config path

Library Usage (if applicable)
=============================

Explain important classes, functions, and workflows.

Example
-------

.. code-block:: python

   from projectname import Simulator

   sim = Simulator(param=42)
   result = sim.compute()

Workflows
=========

Describe recommended workflows or common tasks.

1. Step 1  
2. Step 2  
3. Step 3  

Troubleshooting
===============

Common Issues
-------------

**Problem:** X doesn't work  
**Solution:** Check that Y is installed.

Logging / Debug Mode
--------------------

Explain how users can access debug output.

FAQ
===

Q: How do I do X?  
A: Do Y.

Q: Why doesn’t Z work?  
A: Because you need to enable option B.

Version Compatibility
=====================

Describe compatible versions of Python, dependencies, and OS.

Changelog
=========

Provide a summary or link to a dedicated changelog file.

.. note::
   Full changelog is available in :doc:`changelog`.

License
=======

Full license is available in :doc:`license`

Contact / Support
=================

It is possible to open an issue in GitHub: `<https://github.com/TFYA99ProjGroup/MDSE/issues>`_. 

Note however that this software will not be supported continually after the 16th January 2026 due to :math:`\mathcal{L}\mathcal{I}\mathcal{F}\mathcal{E}`.  

Until then, you can contact our Product owner:
    - oskbo133@student.liu.se
    - Hertz, F-house, Linköping University


