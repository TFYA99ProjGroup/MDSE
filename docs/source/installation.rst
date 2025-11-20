Installation
============

**Open MPI**

In order to run the program parallel on multiple cores, install your favorite MPI. 
For example: Open MPI, follow the installation guide here: https://www.open-mpi.org/software/ompi/v5.0/ 

**Python venv**

Activate a python virtual enviroment either with python venv

.. code-block:: bash

    python3 -m venv venv
    source venv/bin/activate

or with conda enviroment

.. code-block:: bash

    conda create -n mdseenv python=3
    conda activate mdseenv

**Dependencies**

To install the mdse-package, run:

.. code-block:: bash

   python3 -m pip install --upgrade pip
   pip install -e .