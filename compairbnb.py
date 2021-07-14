# Helper functions
import os
import trip
from pymongo import MongoClient
from trip import Listing, Trip

mongodb_uri = os.environ['MONGODB_URI']
client = MongoClient(mongodb_uri)
db=client['compairbnb']
listing_collection = db['listings']
# comment_collection = db['comment']
# vote_collection = db['vote']

trip = Trip('_test', db)
# trip.add_comments(41723684, 'this is a new comment')
# trip.populate_trip()
trip.add_vote(41723684, 'Person', 5)
trip.populate_trip()
print(trip)
# print(trip.get_all_votes(41723684))