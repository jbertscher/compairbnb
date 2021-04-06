import argparse
import airbnb
import glob
import json
from pymongo import MongoClient
import os
import pandas as pd
import pandas.io.formats.format as fmt
import re
import requests

mongodb_uri = os.environ['MONGODB_URI']
client = MongoClient(mongodb_uri)
db=client['compairbnb']

api = airbnb.Api(randomize=True)


def extract_listing_id(url):
    if url:
        re_groups = re.search('www.airbnb.com/rooms/(.*)\?', url)
        if re_groups:
            listing_id = re_groups.group(1)
            return listing_id


def get_listing_json(listing_id):
    try:
        listing_details = api.get_listing_details(listing_id)
        return listing_details
    except requests.exceptions.HTTPError as error:
        print (error)


def parse_beds(listing_json):
    rooms = listing_json['pdp_listing_detail']['listing_rooms']
    num_bed_types = {}
    if len(rooms) > 0:
        for room in rooms:
            for bed in room['beds']:
                bed_type = bed['type']
                bed_quantity = num_bed_types.get(bed_type, 0) + bed['quantity']
                num_bed_types[bed_type] = bed_quantity
    return num_bed_types


def parse_json(listing_json):
    pdp_listing_detail = listing_json['pdp_listing_detail']
    try:
        url = listing_json['url']
    except KeyError:
        url = ''

    num_bed_types = json.dumps(parse_beds(listing_json))

    p = re.compile('^([0-9]*)')
    listing_details = {
        'id': pdp_listing_detail['id'],
        'image': pdp_listing_detail['photos'][0]['large'],
        'url': url,
        'p3_summary_title': pdp_listing_detail['p3_summary_title'],
        'bathroom_label': p.search(listing_json['pdp_listing_detail']['bathroom_label']).group(0),
        'bed_label': p.search(listing_json['pdp_listing_detail']['bed_label']).group(0),
        'bedroom_label': p.search(listing_json['pdp_listing_detail']['bedroom_label']).group(0),
        'guest_label': p.search(listing_json['pdp_listing_detail']['guest_label']).group(0),
        'num_bed_types': num_bed_types,
        'p3_summary_title': listing_json['pdp_listing_detail']['p3_summary_title'],
        'p3_summary_address': listing_json['pdp_listing_detail']['p3_summary_address']
    }
    return listing_details     


def write_listing_from_url(url: str, trip_id: int) -> int:
    # Extract listing id from url
    listing_id = extract_listing_id(url)
    
    # Get listing json and write
    listing = get_listing_json(listing_id)
    if listing:
        listing['trip_id'] = trip_id
        listing['url'] = url[:url.find('?')]  # Strip query parameters
        result = db['listings'].insert_one(listing)
        return result
    else:
        return 1
    

def get_listing_from_file(file_name: str):
    with open(f'{file_name}', 'r') as file:
        listing = file.read()
    listing = json.loads(listing)
    return listing


def combine_listings(listings: list[str]) -> pd.DataFrame:
    if len(listings)>0:
        return pd.concat(listings, axis=0)
    else:
        return pd.DataFrame()


def combine_all_listings(trip_id: int) -> list:
    all_listings = db['listings'].find({'trip_id': trip_id})
    if all_listings.collection.count_documents({})>0:
        all_listings_parsed = []
        
        for listing in all_listings:
            listing_parsed = parse_json(listing)
            listing_parsed = pd.DataFrame(listing_parsed, index=[listing_parsed['id']])
            all_listings_parsed.append(listing_parsed)

        return combine_listings(all_listings_parsed)
    else:
        return pd.DataFrame()


def delete_listing(listing_id: int, trip_id: int) -> None:
    db['listings'].delete_one({'trip_id': trip_id, 'pdp_listing_detail.id': listing_id})
    

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('command')
    parser.add_argument('--listing_id')
    parser.add_argument('--filename')
    args = parser.parse_args()
    
    command = args.command
    filename = args.filename
    listing_id = args.listing_id

    if command=='write_file':
        with open(filename, 'w') as file:
            listing = get_listing_json(listing_id)
            json.dump(listing, file)
        print(f'Listing written to {filename}!')
    elif command=='get':
        print(combine_all_listings())

    # python compairbnb.py write_file --listing_id 7609356 --filename 7609356.json

    # print(db['listings'].find()[0])
    # print(combine_all_listings(123))
    # write_listing_from_url('https://www.airbnb.com/rooms/29585414?federated_search_id=5167759d-28c9-4808-a841-9dd9034d162b&source_impression_id=p3_1616531404_0NAyCuUgacR16cW9', 123)
    # db['listings'].delete_many({})

    