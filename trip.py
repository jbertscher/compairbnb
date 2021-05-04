import os
from socket import send_fds
import airbnb
import json
import pandas as pd
from pymongo import MongoClient, mongo_client
from pymongo.collection import Collection
import re
import requests

# # TODO:
# + Reload table after submitting new url without reloading (now that page doesn't reload)
# + Clear new url from text box after submit
# + How to properly write test functions in Python
# + When to store in memory and when to read from db

class Listing:
    # api = airbnb.Api(randomize=True)
    api = airbnb.Api(api_key='d306zoyjsyarp7ifhu67rjxn52tv0t20', randomize=True)

    def __init__(self, listing_id: int, url: str, trip_id: str, raw_listing_json: str = None, 
        properties: str = None):

        assert isinstance(listing_id, int)
        assert isinstance(trip_id, str)
        
        self.listing_id = listing_id
        self.url = url
        self.trip_id = trip_id
        self.raw_listing_json = raw_listing_json
        self.properties = properties

    def populate_listing_properties(self):
        self.raw_listing_json = Listing.get_raw_json(self)
        self.properties = Listing.get_properties_from_raw_json(self)

    def write_to_db(self, collection: Collection) -> int:
        '''
        Writes Listing to DB. Returns the result retured by insert_one()  
        '''        
        if self.raw_listing_json:
            result = collection.insert_one(
                {
                    'listing_id': int(self.listing_id),
                    'url': self.url,
                    'trip_id': self.trip_id,
                    'raw_listing_json': self.raw_listing_json,
                    'properties': self.properties    
                }
            )
            return result

    @classmethod
    def create_from_id(cls, listing_id, trip_id):
        url = f'https://www.airbnb.com/rooms/{listing_id}]'
        return cls(listing_id, url, trip_id)

    @classmethod
    def create_from_url(cls, url, trip_id):
        # Strip query parameters, if there are any
        if '?' in url:
            url = url[:url.find('?')]  
        listing_id = int(cls.extract_id(url))
        return cls(listing_id, url, trip_id)

    @classmethod
    def read_from_db(cls, listing_id, trip_id, collection: Collection):
        assert isinstance(trip_id, str)
        
        result = collection.find_one({'listing_id': listing_id, 'trip_id': trip_id})
        return cls(result['listing_id'], result['url'], result['trip_id'], result['raw_listing_json'], result['properties'])

    @classmethod
    def get_raw_json(cls, listing):
        try:
            raw_listing_json = cls.api.get_listing_details(listing.listing_id)
            return raw_listing_json
        except requests.exceptions.HTTPError as error:
            print (error)
            return None

    @classmethod
    def get_properties_from_raw_json(cls, listing):
        pdp_listing_detail = listing.raw_listing_json['pdp_listing_detail']

        try:
            url = listing.url
        except KeyError:
            url = ''

        p = re.compile('^([0-9]*)')
        properties = {
            'listing_id': pdp_listing_detail['id'],
            'image': pdp_listing_detail['photos'][0]['large'],
            'url': url,
            'p3_summary_title': pdp_listing_detail['p3_summary_title'],
            'bathroom_label': p.search(listing.raw_listing_json['pdp_listing_detail']['bathroom_label']).group(0),
            'bed_label': p.search(listing.raw_listing_json['pdp_listing_detail']['bed_label']).group(0),
            'bedroom_label': p.search(listing.raw_listing_json['pdp_listing_detail']['bedroom_label']).group(0),
            'guest_label': p.search(listing.raw_listing_json['pdp_listing_detail']['guest_label']).group(0),
            'num_bed_types': json.dumps(cls.parse_beds(listing)),
            'p3_summary_title': listing.raw_listing_json['pdp_listing_detail']['p3_summary_title'],
            'p3_summary_address': listing.raw_listing_json['pdp_listing_detail']['p3_summary_address']
        }
        return properties     

    @staticmethod
    def delete_listing(listing_id: int, trip_id: str, collection: Collection) -> None:
        collection.delete_one({'trip_id': trip_id, 'listing_id': listing_id})
    
    @staticmethod
    def extract_id(url):
        if url:
            re_groups = re.search('www.airbnb.com/rooms/([0-9]*).*', url)
            if re_groups:
                listing_id = re_groups.group(1)
                return listing_id
            
    @staticmethod
    def parse_beds(listing):
        rooms = listing.raw_listing_json['pdp_listing_detail']['listing_rooms']
        num_bed_types = {}
        if len(rooms) > 0:
            for room in rooms:
                for bed in room['beds']:
                    bed_type = bed['type']
                    bed_quantity = num_bed_types.get(bed_type, 0) + bed['quantity']
                    num_bed_types[bed_type] = bed_quantity
        return num_bed_types

    @staticmethod
    def write_listing_from_url(url: str, trip_id: int, collection: Collection) -> int:
        listing = Listing.create_from_url(url, trip_id)
        listing.populate_listing_properties()
        
        if listing.properties:
            return listing.write_to_db(collection)
        else:
            return 1


class Trip:
    def __init__(self, trip_id, collection, all_listing_properties: pd.DataFrame = None):
        self.trip_id = trip_id
        self.collection = collection
        self.all_listing_properties = all_listing_properties

    def populate_trip(self):
        self.all_listing_properties = self.get_and_combine_all_listings()

    def get_all_listings(self):
        all_listing_records = self.collection.find({'trip_id': self.trip_id})
        # if all_listing_records.collection.count_documents({})>0:
        all_listings = []
        for listing_record in all_listing_records:
            listing = Listing(listing_record['listing_id'], listing_record['url'], listing_record['trip_id'], 
                listing_record['raw_listing_json'], listing_record['properties'])
            all_listings.append(listing)
        return all_listings
        
    def get_and_combine_all_listings(self):
        all_listings = self.get_all_listings()
        if all_listings and len(all_listings) > 0:
            all_listings_pd = []
            for listing in all_listings:
                listing_df = pd.DataFrame(listing.properties, index=[listing.listing_id])
                all_listings_pd.append(listing_df)

            return self.combine_listings(all_listings_pd)
        else:
            return pd.DataFrame()

    def delete_listing(self, listing_id) -> None:
        Listing.delete_listing(listing_id, self.trip_id, self.collection)
        # If results have been cached, remove from the DataFrame as well as DB
        if self.all_listing_properties:
            self.all_listing_properties = self.all_listing_properties.loc[~listing_id]

    @staticmethod
    def combine_listings(listings: list[str]) -> pd.DataFrame:
        if len(listings)>0:
            return pd.concat(listings, axis=0)
        else:
            return pd.DataFrame()

def test_populate_trips(collection, method):
    if method=='url':
        urls = ['https://www.airbnb.com/rooms/45797974', 'https://www.airbnb.com/rooms/22023500?q=123']
        for url in urls:
            listing = Listing.create_from_url(url, '_test')    
            listing.populate_listing_properties()
            listing.write_to_db(collection)

def test_get_and_combine_all_listings(collection):
    listings = Trip('_test', collection).get_and_combine_all_listings()
    return listings

def test_read_from_db():
    # print(Listing.read_from_db(34455224, '3', collection))
    found_listing = Listing.read_from_db(45797974, '5', collection)
    found_listing.populate_listing_properties()
    return found_listing.raw_listing_json

if __name__=='__main__':
    mongodb_uri = os.environ['MONGODB_URI']
    client = MongoClient(mongodb_uri)
    db=client['compairbnb']

    trip = Trip('_test', db['listings'])
    trip.populate_trip()
    print(trip.all_listing_properties)
    print('done!')
