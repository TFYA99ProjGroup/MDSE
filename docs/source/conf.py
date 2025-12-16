# Copyright (c) 2025 See AUTHORS
#
# This work is licensed under the terms of the MIT license.
# For a copy, see <https://github.com/TFYA99ProjGroup/MDSE/blob/main/LICENSE>.


# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

import os
import sys

sys.path.insert(0, os.path.abspath("../../src/mdse"))

project = "MDSE"
copyright = "2025, A. Emil, B. Oskar, J. Petter, K. Axel, M. Patrik, S. Lukas"
author = "A. Emil, B. Oskar, J. Petter, K. Axel, M. Patrik, S. Lukas"
release = "1.0.0"

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.autosummary",
    "sphinx.ext.napoleon",  # for Google/NumPy style docstrings
]
autosummary_generate = True

templates_path = ["_templates", "_templates/apidoc"]
exclude_patterns = []

# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

html_theme = "sphinx_rtd_theme"
html_static_path = ["_static"]

autodoc_default_options = {
    "members": True,
    "undoc-members": False,
    "private-members": False,
    "special-members": False,
    "inherited-members": False,
    "show-inheritance": True,
}

# Mock external dependencies
autodoc_mock_imports = ["mpi4py", "mpi4py.MPI", "e3nn"]

# -- Options for PDF output -------------------------------------------------

latex_elements = {
    'classoptions': 'raggedright',
}
