from pymongo import MongoClient


def test_set_up_database():
    # Connect to MongoDB on localhost
    client = MongoClient("mongodb://localhost:27017/")
