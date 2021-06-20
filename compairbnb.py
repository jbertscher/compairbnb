# Helper functions
import os
import trip
from pymongo import MongoClient
from trip import Listing, Trip

mongodb_uri = os.environ['MONGODB_URI']
client = MongoClient(mongodb_uri)
db=client['compairbnb']
listing_collection = db['listings']
comment_collection = db['comments']

# listing = Listing.create_from_id(48524521, '_test')
# listing.add_comments('comments 20 June 10:25', listing_collection)
# listing = listing_collection.find_one({'listing_id': 48524521, 'trip_id': '_test'})
# print(listing)

trip = Trip('_test', listing_collection, comment_collection)
trip.populate_trip(True)
listing = Listing.create_from_id(41723684, '_test')
trip.add_comments(41723684, 'x')
# listing.add_comments('comments 20 June 15:45', comment_collection)
print(trip.get_comments(41723684, comment_collection))

# print(trip.get_comments(41723684, comment_collection))
# listing = trip.get_listing(41723684)
# comments = trip.get_comments(41723684, comment_collection)
# comments = listing.get_comments(comment_collection)
# print('comments:')
# print(comments)
# listing_collection.update_one(
#     {'listing_id': 48524521, 'trip_id': '_test'}, 
#     {'$set': {'comments': 'this is a comments three'}}
# )

# print(trip.all_listing_properties)

# for trip_id in trip.all_listing_properties.index:
#     trip.delete_listing(trip_id, delete_from_cache=False)
# trip.populate_trip()
# print(trip.all_listing_properties)

# Trip('_test', listing_collection).add_comments('41723684', 'this is a comments')
# print('x')