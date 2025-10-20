#!/usr/bin/env python3
from ase.collections import g2
from ase.build.molecule import extra

print("Allowed Common Molecules:")
print(g2.names)
print("\nExtra:")
print(extra.keys())
