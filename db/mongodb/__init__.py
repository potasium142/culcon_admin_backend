from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi
from config import env

uri = env.MONGODB_URL

# Create a new client and connect to the server
# client = MongoClient(uri, server_api=ServerApi("1"))

# db = client.Culcon

db = None
