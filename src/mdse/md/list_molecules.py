# Copyright (c) 2025 See AUTHORS
#
# This work is licensed under the terms of the MIT license.
# For a copy, see <https://github.com/TFYA99ProjGroup/MDSE/blob/main/LICENSE>.


#!/usr/bin/env python3
from ase.collections import g2
from ase.build.molecule import extra

print("Allowed Common Molecules:")
print(g2.names)
print("\nExtra:")
print(extra.keys())
