# Copyright (c) 2025 See AUTHORS
#
# This work is licensed under the terms of the MIT license.
# For a copy, see <https://github.com/TFYA99ProjGroup/MDSE/blob/main/LICENSE>.


from mdse.rm.runmanager import RunManager

def test_init_without_config():
    rm = RunManager()

    assert rm.md_simulations == []
