from __future__ import annotations
import os
from socket import send_fds
import airbnb
import json
import pandas as pd
from pymongo import MongoClient, mongo_client
from pymongo.collection import Collection
from pymongo.results import InsertOneResult
import re
import requests
from typing import Optional

# # TODO:
# + Add features:
# ++ price
# ++ commenting for single user
# ++ commenting for multiple users
# + Implement testing
# + When to store in memory and when to read from db (take into account different users using same trip at same time)
# + think about allowing users to log in so using their own access tokens

AIRBNB_API_KEY = os.environ['AIRBNB_API_KEY']

class Listing:
    api = airbnb.Api(api_key=AIRBNB_API_KEY, randomize=True)


    def __init__(self, listing_id: int, url: str, trip_id: str, raw_listing_json: str = Optional[None], properties: str = Optional[None]) -> None:
        assert isinstance(listing_id, int), 'listing_id must be Integer'
        assert isinstance(trip_id, str), 'trip_id must be String'
        
        self.listing_id = listing_id
        self.url = url
        self.trip_id = trip_id
        self.raw_listing_json = raw_listing_json
        self.properties = properties


    def populate_listing_properties(self) -> None:
        '''
        Populates trip with listings data.
        '''
        self.raw_listing_json = Listing.get_raw_json(self)
        self.properties = Listing.get_properties_from_raw_json(self)


    def write_to_db(self, collection: Collection) -> InsertOneResult:
        '''
        Writes Listing to DB. Returns the result retured by insert_one().
        '''        
        # Don't write if listing id already found for that trip
        if not collection.find_one({'listing_id' : self.listing_id, 'trip_id': self.trip_id}): 
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
    def create_from_id(cls, listing_id: int, trip_id: str) -> Listing:
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
            'num_bed_types': cls.parse_beds(listing),
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
        listing.write_to_db(collection)


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
            all_listings_combined = []
            for listing in all_listings:
                all_listings_combined.append(listing.properties)
            return all_listings_combined
        else:
            return []


    def delete_listing(self, listing_id: str, delete_from_cache: bool = True) -> None:
        '''
        Deletes a listing from the database and from cache by detault. Be careful deleting from cache when looping though all the listings
        as this has side-effects. In that case, use delete_from_cache = False.
        '''
        Listing.delete_listing(listing_id, self.trip_id, self.collection)
        # If results have been cached, remove from the DataFrame as well as DB
        # if self.all_listing_properties is not None and delete_from_cache:
        #     self.all_listing_properties = self.all_listing_properties.loc[~listing_id]
    

    def write_listing_from_url(self, url: str):
        listing = Listing.create_from_url(url, self.trip_id)
        listing.populate_listing_properties()
        listing.write_to_db(self.collection)


    @staticmethod
    def combine_listings(listings: list[pd.DataFrame]) -> pd.DataFrame:
        if len(listings)>0:
            return pd.concat(listings, axis=0)
        else:
            return pd.DataFrame()

