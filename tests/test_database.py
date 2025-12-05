# Copyright (c) 2025 See AUTHORS
#
# This work is licensed under the terms of the MIT license.
# For a copy, see <https://opensource.org/licenses/MIT>.
#
# SPDX-License-Identifier: MIT

from pymongo import MongoClient


def test_set_up_database():
    # Connect to MongoDB on localhost
    client = None
    client = MongoClient("mongodb://localhost:27017/")
    assert client is not None
