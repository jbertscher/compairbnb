import airbnb
import json
import re
import requests

class Listing:
    api = airbnb.Api(randomize=True)

    def __init__(self, listing_id, listing_url=None, listing_json=None):
        self.listing_id = listing_id
        self.listing_url = listing_url
        self.listing_json = listing_json

    @classmethod
    def get_listing_json(cls, listing):
        try:
            listing_details = cls.api.get_listing_details(listing.listing_id)
            return listing_details
        except requests.exceptions.HTTPError as error:
            print (error)

    @classmethod
    def parse_json(cls, listing):
        pdp_listing_detail = listing.listing_json['pdp_listing_detail']
        try:
            url = listing.listing_json['url']
        except KeyError:
            url = ''

        num_bed_types = json.dumps(cls.parse_beds(listing.listing_json))

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

        
    
