import argparse
import airbnb
from flask_table import Table, Col, create_table
import glob
import json
import pandas as pd
import pandas.io.formats.format as fmt


LISTINGS_DIR = 'saved_listings'

api = airbnb.Api(randomize=True)


def extract_listing_id(url):
    import re
    listing_id = re.search('www.airbnb.com/rooms/(.*)\?', url).group(1)
    return listing_id


def read_listing(listing_id):
    # Writes to string
    # return json.dumps(api.get_listing_details(listing_id))
    return api.get_listing_details(listing_id)


def parse_json(listing_json):
    # return pd.json_normalize(json_input['pdp_listing_detail']['listing_amenities'])
    pdp_listing_detail = listing_json['pdp_listing_detail']

    listing_details = {
        'id': pdp_listing_detail['id'],
        'p3_summary_title': pdp_listing_detail['p3_summary_title'],
        'bathroom_label': listing_json['pdp_listing_detail']['bathroom_label'],
        'bed_label': listing_json['pdp_listing_detail']['bed_label'],
        'bedroom_label': listing_json['pdp_listing_detail']['bedroom_label'],
        'guest_label': listing_json['pdp_listing_detail']['guest_label'],
        'p3_summary_title': listing_json['pdp_listing_detail']['p3_summary_title'],
        'p3_summary_address': listing_json['pdp_listing_detail']['p3_summary_address']
    }
    return listing_details     


def write_listing_from_url(url):
    # Extract listing id from url
    listing_id = extract_listing_id(url)
    
    # Get listing json and write
    listing = read_listing(listing_id)
    with open(f'{LISTINGS_DIR}/{listing_id}.json', 'w') as file:
        json.dump(listing, file)


def get_listing_from_file(file_name):
    with open(f'{file_name}', 'r') as file:
        listing = file.read()
    listing = json.loads(listing)
    return listing


def combine_listings(listings: list[str]):
    return pd.concat(listings, axis=0)


def combine_all_listings(listings_dir: str):
    all_listings_parsed = []
    for listing_file in glob.glob(f'{listings_dir}/*'):
        listing = get_listing_from_file(listing_file)
        listing_parsed = parse_json(listing)
        listing_parsed = pd.DataFrame(listing_parsed, index=[listing_parsed['id']])
        all_listings_parsed.append(listing_parsed)

    all_listings_combined = combine_listings(all_listings_parsed)
    return all_listings_combined

def create_html_table(df):
    # class Results(Table):
    #     cols = []
    #     for col in df.columns.tolist():
    #         new_col = Col(col)
    #         cols.append(new_col)

    df = df.reset_index()
    df.columns = df.columns.astype('str')
    items = df.to_dict(orient='records')

    Results = create_table('Results')
    for col in df.columns.tolist():
        Results.add_column(col, Col(col))

    results = Results(items)
    return results

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




    

    