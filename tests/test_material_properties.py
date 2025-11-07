import pytest
import numpy as np
from mdse.rm.runmanager import RunManager
from mdse.md.resultMD import ResultMD

def run_simulations():
    config = main_read("material_test.yaml")

    rm = RunManager(config)

    