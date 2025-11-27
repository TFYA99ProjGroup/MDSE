import os
import pytest


@pytest.fixture
def address():
    if os.getenv("GITHUB_ACTIONS") == "true":
        return "mongodb://admin:secret@localhost:27017/"
    else:
        return "mongodb://admin:secret@localhost:27017/"
