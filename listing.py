import os
from socket import send_fds
import airbnb
import json
from pymongo import MongoClient, mongo_client
from pymongo.collection import Collection
import re
import requests

# TODO:
# 1. Figure out if want to be able to create instance of Listing only with id or with only url or both?

class Listing:
    api = airbnb.Api(randomize=True)

    def __init__(self, listing_id, trip_id, listing_url=None, listing_json=None, listing_details=None):
        self.listing_id = listing_id
        self.trip_id = trip_id
        self.listing_url = listing_url
        self.listing_json = listing_json
        self.listing_details = listing_details

    def get_and_parse_data(self):
        self.listing_url()
        self.listing_json = Listing.get_listing_json(self)
        self.listing_details = Listing.parse_json(self)

    def write_listing(self, db: Collection) -> int:
        # Get listing json and write
        listing_json = self.listing_json
        if listing_json:
            listing_json['trip_id'] = self.trip_id
            listing_json['url'] = self.listing_url[:self.listing_url.find('?')]  # Strip query parameters
            result = db['listings'].insert_one(listing_json)
            return result
        else:
            return 1

    @classmethod
    def get_listing_json(cls, listing):
        try:
            listing_details = cls.api.get_listing_details(listing.listing_id)
            return listing_details
        except requests.exceptions.HTTPError as error:
            print (error)
            return None

    @classmethod
    def parse_json(cls, listing):
        pdp_listing_detail = listing.listing_json['pdp_listing_detail']
        try:
            url = listing.listing_json['url']
        except KeyError:
            url = ''

        num_bed_types = json.dumps(cls.parse_beds(listing))

        p = re.compile('^([0-9]*)')
        listing_details = {
            'id': pdp_listing_detail['id'],
            'image': pdp_listing_detail['photos'][0]['large'],
            'url': url,
            'p3_summary_title': pdp_listing_detail['p3_summary_title'],
            'bathroom_label': p.search(listing.listing_json['pdp_listing_detail']['bathroom_label']).group(0),
            'bed_label': p.search(listing.listing_json['pdp_listing_detail']['bed_label']).group(0),
            'bedroom_label': p.search(listing.listing_json['pdp_listing_detail']['bedroom_label']).group(0),
            'guest_label': p.search(listing.listing_json['pdp_listing_detail']['guest_label']).group(0),
            'num_bed_types': num_bed_types,
            'p3_summary_title': listing.listing_json['pdp_listing_detail']['p3_summary_title'],
            'p3_summary_address': listing.listing_json['pdp_listing_detail']['p3_summary_address']
        }

        return listing_details     

    @staticmethod
    def extract_listing_id(url):
        if url:
            re_groups = re.search('www.airbnb.com/rooms/(.*)\?', url)
            if re_groups:
                listing_id = re_groups.group(1)
                return listing_id
            
    @staticmethod
    def parse_beds(listing):
        rooms = listing.listing_json['pdp_listing_detail']['listing_rooms']
        num_bed_types = {}
        if len(rooms) > 0:
            for room in rooms:
                for bed in room['beds']:
                    bed_type = bed['type']
                    bed_quantity = num_bed_types.get(bed_type, 0) + bed['quantity']
                    num_bed_types[bed_type] = bed_quantity
        return num_bed_types

    @staticmethod
    def write_listing_from_url(url: str, trip_id: int, db: Collection) -> int:
        # Extract listing id from url
        listing_id = Listing.extract_listing_id(url)
        
        # Get listing json and write
        listing = Listing.get_listing_json(listing_id)
        if listing:
            listing['trip_id'] = trip_id
            listing['url'] = url[:url.find('?')]  # Strip query parameters
            result = db['listings'].insert_one(listing)
            return result
        else:
            return 1

if __name__=='__main__':
    listing = Listing(4166953, 4)
    listing.get_and_parse_data()
    print(listing.listing_details)

    mongodb_uri = os.environ['MONGODB_URI']
    client = MongoClient(mongodb_uri)
    db=client['compairbnb']
    listing.write_listing(db)


