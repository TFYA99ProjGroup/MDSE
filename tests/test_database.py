from pymongo import MongoClient

# Connect to MongoDB on localhost
client = MongoClient("mongodb://localhost:27017/")

# Test the connection
print(client.list_database_names())
