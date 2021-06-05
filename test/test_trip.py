import os
from pymongo import MongoClient

mongodb_uri = os.environ['MONGODB_URI']
client = MongoClient(mongodb_uri)
db=client['compairbnb']
collection = db['listings']