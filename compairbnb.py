# Helper functions
import os
import trip
from pymongo import MongoClient
from trip import Listing, Trip

mongodb_uri = os.environ['MONGODB_URI']
client = MongoClient(mongodb_uri)
db=client['compairbnb']
listing_collection = db['listings']

trip = Trip('_test', listing_collection)
trip.populate_trip()
print(trip.all_listing_properties)
for trip_id in trip.all_listing_properties.index:
    trip.delete_listing(trip_id, delete_from_cache=False)
trip.populate_trip()
print(trip.all_listing_properties)