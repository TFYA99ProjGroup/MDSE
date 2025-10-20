Example
============
**Run your first simulation**

To simulate you use the command simulate:

.. code-block:: bash
    
    mdse simulate --filepath examples/multiple_md.yaml

So called .traj-files will appear in the current working directory. These can be viewed with:

.. code-block:: bash

    mdse view

The .traj files can be removed with:

.. code-block:: bash

    mdse clean


Both view and clean can specify filepath with --filepath. 