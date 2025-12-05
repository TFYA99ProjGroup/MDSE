# Copyright (c) 2025 See AUTHORS
#
# This work is licensed under the terms of the MIT license.
# For a copy, see <https://opensource.org/licenses/MIT>.
#
# SPDX-License-Identifier: MIT

import os
import pytest


@pytest.fixture
def address():
    if os.getenv("GITHUB_ACTIONS") == "true":
        return "mongodb://admin:secret@localhost:27017/"
    else:
        return "mongodb://admin:secret@localhost:27017/"
