import argparse
import airbnb
import glob
import json
import os
import pandas as pd
import pandas.io.formats.format as fmt
import re
import requests


LISTINGS_DIR = 'saved_listings'

api = airbnb.Api(randomize=True)


def extract_listing_id(url):
    if url:
        re_groups = re.search('www.airbnb.com/rooms/(.*)\?', url)
        if re_groups:
            listing_id = re_groups.group(1)
            return listing_id


def read_listing(listing_id):
    try:
        listing_details = api.get_listing_details(listing_id)
        return listing_details
    except requests.exceptions.HTTPError as error:
        print (error)


def parse_json(listing_json):
    # return pd.json_normalize(json_input['pdp_listing_detail']['listing_amenities'])
    pdp_listing_detail = listing_json['pdp_listing_detail']

    p = re.compile('^([0-9]*)')
    listing_details = {
        'id': pdp_listing_detail['id'],
        'p3_summary_title': pdp_listing_detail['p3_summary_title'],
        'bathroom_label': p.search(listing_json['pdp_listing_detail']['bathroom_label']).group(0),
        'bed_label': p.search(listing_json['pdp_listing_detail']['bed_label']).group(0),
        'bedroom_label': p.search(listing_json['pdp_listing_detail']['bedroom_label']).group(0),
        'guest_label': p.search(listing_json['pdp_listing_detail']['guest_label']).group(0),
        'p3_summary_title': listing_json['pdp_listing_detail']['p3_summary_title'],
        'p3_summary_address': listing_json['pdp_listing_detail']['p3_summary_address']
    }
    return listing_details     


def write_listing_from_url(url):
    # Extract listing id from url
    listing_id = extract_listing_id(url)
    
    # Get listing json and write
    listing = read_listing(listing_id)
    if listing:
        with open(f'{LISTINGS_DIR}/{listing_id}.json', 'w') as file:
            json.dump(listing, file)
            return 0
    return 1
    

def get_listing_from_file(file_name):
    with open(f'{file_name}', 'r') as file:
        listing = file.read()
    listing = json.loads(listing)
    return listing


def combine_listings(listings: list[str]):
    return pd.concat(listings, axis=0)


def combine_all_listings(listings_dir: str) -> list:
    if len(glob.glob1(listings_dir, '*.json')) > 0:
        all_listings_parsed = []
        for listing_file in glob.glob(f'{listings_dir}/*.json'):
            listing = get_listing_from_file(listing_file)
            listing_parsed = parse_json(listing)
            listing_parsed = pd.DataFrame(listing_parsed, index=[listing_parsed['id']])
            all_listings_parsed.append(listing_parsed)

        return combine_listings(all_listings_parsed)
    else:
        return pd.DataFrame()


def delete_listing(listing_id):
    os.replace(f'{LISTINGS_DIR}/{listing_id}.json', f'{LISTINGS_DIR}/deleted/{listing_id}.json')
    

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('command')
    parser.add_argument('--url')
    args = parser.parse_args()
    
    command = args.command
    url = args.url

    if command=='add':
        write_listing_from_url(url)
        print('Listing added!')
    elif command=='get':
        print(combine_all_listings(LISTINGS_DIR))




    

    