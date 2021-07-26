from __future__ import annotations
import os
from socket import send_fds
import airbnb  # https://github.com/nderkach/airbnb-python
import json
import pandas as pd
from pymongo.collection import Collection
from pymongo.database import Database
from pymongo.results import InsertOneResult
import re
import requests
from typing import List, Optional, Union

# TODO - ITERATION 1:
# + Add features:
# ++ favouriting (allow adding columns with names of different users)
# +++ Implement adding voter column (need collection to store votes)
# +++ Implement delete voter column (use right click function)
# ++ Ability to add and remove columns with menu function
# + Look into why get_and_combine_all_listings() takes so long now and see if speed can be improved (is it because now looking at comments db as well?)
# + Implement basic testing
# + Create readme, document, and make live on git 

# TODO - ITERATION 2:
# + Improve performance by reading all data at once instead of iterating through listings
# + Add price: requires calling a different API endpoint: https://www.airbnb.com/api/v3/StaysPdpSections but this isn't implemented in the airbnb library that I'm using
# + Add commenting for multiple users
# + Homepage for generating trips
# + Ability to add users based (allowing login, maybe using Google account)
# + Chrome extension for adding properties


AIRBNB_API_KEY = os.environ['AIRBNB_API_KEY']


class Listing:
    api = airbnb.Api(api_key=AIRBNB_API_KEY, randomize=True)


    def __init__(self, listing_id: int, url: str, trip_id: str, raw_listing_json: str = Optional[None], 
        properties: str = Optional[None], comments: str = Optional[None], votes: str = Optional[None]) -> None:
        
        assert isinstance(listing_id, int), 'listing_id must be Integer'
        assert isinstance(trip_id, str), 'trip_id must be String'
        
        self.listing_id = listing_id
        self.url = url
        self.trip_id = trip_id
        self.raw_listing_json = raw_listing_json
        self.properties = properties
        self.comments = comments
        self.votes = votes


    def populate_listing_properties(self) -> None:
        self.properties = Listing.get_properties_from_raw_json(self)


    def populate_comments(self, listing_collection: Collection) -> None:
        self.comments = self.get_comments(listing_collection)


    def write_to_db(self, listing_collection: Collection) -> InsertOneResult:
        '''
        Writes Listing to DB. Returns the result retured by insert_one().
        '''        
        # Don't write if listing id already found for that trip
        if not listing_collection.find_one({'listing_id' : self.listing_id, 'trip_id': self.trip_id}): 
            if self.raw_listing_json:
                result = listing_collection.insert_one(
                    {
                        'listing_id': int(self.listing_id),
                        'url': self.url,
                        'trip_id': self.trip_id,
                        'raw_listing_json': self.raw_listing_json,
                        'properties': self.properties
                    }
                )
                return result


    def add_comments(self, comments: str, listing_collection: Collection) -> None:
        listing_collection.update_one(
            {
                'listing_id': self.listing_id, 
                'trip_id': self.trip_id
            }, 
            {
                '$set': {'comments': comments}
            },
            upsert=True
        )


    def add_vote(self, user: str, points: int, listing_collection: Collection) -> None:
        listing_collection.update_one(
            {
                'listing_id': self.listing_id, 
                'trip_id': self.trip_id,
            }, 
            # {
            #     '$set': {
            #         'votes': {
            #             str(user): points
            #         }
            #     }
            # },
            {
                '$set': {
                    f'votes.{str(user)}': 
                        points
                    
                }
            },
            upsert=True
        )


    def get_listing_data(self, populate_listing_properties:bool = True) -> dict:
        if populate_listing_properties:
            self.populate_listing_properties()
        # Return all the relevant listing data
        listing_data = self.properties
        listing_data['comments'] = self.comments
        listing_data['votes'] = self.votes
        return listing_data


    @classmethod
    def create_from_id(cls, listing_id: int, trip_id: str) -> Listing:
        url = f'https://www.airbnb.com/rooms/{listing_id}]'
        return cls(listing_id, url, trip_id)


    @classmethod
    def create_from_url(cls, url: str, trip_id: str):
        # Strip query parameters, if there are any
        if '?' in url:
            url = url[:url.find('?')]  
        listing_id = int(cls.extract_id(url))
        return cls(listing_id, url, trip_id)


    @classmethod
    def create_from_db(cls, listing_id: int, trip_id: str, listing_collection: Collection):
        assert isinstance(trip_id, str)
        
        listing_data = listing_collection.find_one({'listing_id': listing_id, 'trip_id': trip_id})
        
        return cls(listing_id, listing_data['url'], trip_id, listing_data['raw_listing_json'], listing_data['properties'], 
            listing_data['comments'], listing_data['votes'])


    @classmethod
    def get_raw_json(cls, listing: Listing):
        try:
            raw_listing_json = cls.api.get_listing_details(listing.listing_id)
            return raw_listing_json
        except requests.exceptions.HTTPError as error:
            print (error)
            return None


    @classmethod
    def get_properties_from_raw_json(cls, listing: Listing) -> json:
        pdp_listing_detail = listing.raw_listing_json['pdp_listing_detail']
        try:
            url = listing.url
        except KeyError:
            url = ''

        # Accounts for edge case where there are no reviews
        if len(listing.raw_listing_json['pdp_listing_detail']['reviews_module'])==0:
            localized_overall_rating = "No ratings yet"
        else:
            localized_overall_rating = listing.raw_listing_json['pdp_listing_detail']['reviews_module']['localized_overall_rating']

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
            'p3_summary_address': listing.raw_listing_json['pdp_listing_detail']['p3_summary_address'],
            'localized_overall_rating': localized_overall_rating
        }
        return properties     


    @staticmethod
    def delete_listing(listing_id: int, trip_id: str, listing_collection: Collection) -> None:
        listing_collection.delete_one({'trip_id': trip_id, 'listing_id': listing_id})
    

    @staticmethod
    def extract_id(url: str) -> Union[int, None]:
        if url:
            re_groups = re.search('www.airbnb.com/rooms/([0-9]*).*', url)
            if re_groups:
                listing_id = re_groups.group(1)
                return listing_id
            

    @staticmethod
    def parse_beds(listing: Listing) -> dict:
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
    def write_listing_from_url(url: str, trip_id: str, listing_collection: Collection) -> InsertOneResult:
        listing = Listing.create_from_url(url, trip_id)
        listing.populate_listing_properties()
        listing.write_to_db(listing_collection)


class Trip:
    def __init__(self, trip_id: str, db: Database, 
        all_listing_properties: pd.DataFrame = Optional[None]) -> None:

        self.trip_id = trip_id
        self.listing_collection = db['listings']
        self.all_listing_properties = all_listing_properties


    def populate_trip(self, reparse_raw_json: bool = True) -> None:
        self.all_listing_properties = self.get_and_combine_all_listings(reparse_raw_json)


    def get_and_combine_all_listings(self, reparse_raw_json: bool = True) -> List[dict]:
        all_listings = self.get_all_listings(reparse_raw_json)
        if all_listings and len(all_listings) > 0:
            all_listings_combined = []
            for listing in all_listings:
                listing_data = listing.get_listing_data()
                all_listings_combined.append(listing_data)
            return all_listings_combined
        else:
            return []


    def get_all_listings(self, reparse_raw_json: bool = False) -> list[Listing]:
        all_listing_records = self.listing_collection.find({'trip_id': self.trip_id})
        if all_listing_records.collection.count_documents({})>0:
            all_listings = []
            for listing_record in all_listing_records:
                listing = Listing(listing_record['listing_id'], listing_record['url'], listing_record['trip_id'], 
                    listing_record['raw_listing_json'], listing_record.get('properties'), listing_record.get('comments'), listing_record.get('votes'))
                if reparse_raw_json:
                    listing.populate_listing_properties()
                all_listings.append(listing)
            return all_listings


    def get_listing(self, listing_id: int) -> dict:
        listing = Listing.create_from_id(listing_id, self.trip_id)
        listing.populate_listing()
        return listing
        

    def delete_listing(self, listing_id: str) -> None:
        '''
        Deletes a listing from the database
        '''
        Listing.delete_listing(listing_id, self.trip_id, self.listing_collection)
        self.populate_trip()
    

    def write_listing_from_url(self, url: str) -> None:
        listing = Listing.create_from_url(url, self.trip_id)
        listing.populate_listing_properties()
        listing.write_to_db(self.listing_collection)

    
    def add_comments(self, listing_id: str, comments: str) -> None:
        Listing.create_from_id(listing_id, self.trip_id).add_comments(comments, self.listing_collection)


    def add_vote(self, listing_id: str, user: str, points: int) -> None:
        Listing.create_from_id(listing_id, self.trip_id).add_vote(user, points, self.listing_collection)


    @staticmethod
    def combine_listings(listings: list[pd.DataFrame]) -> pd.DataFrame:
        if len(listings)>0:
            return pd.concat(listings, axis=0)
        else:
            return pd.DataFrame()

