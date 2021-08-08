import argparse
from datetime import datetime
import os
from pymongo import MongoClient
from pymongo.collection import Collection


mongodb_uri = os.environ['MONGODB_URI']
client = MongoClient(mongodb_uri)
db = client['compairbnb']
admin_collection = db['admin']


def update_submit_count(admin_collection: Collection, count: int) -> None:
    admin_collection.update_one(
        {
            'scope': 'app'
        },
        {
            '$set': {
                'submit_count': count,
                'last_submit': datetime.now()
            }
        },
        upsert=True
    )


def increment_submit_count(admin_collection: Collection) -> int:
    update_submit_count(admin_collection,
                        read_submit_count(admin_collection) + 1)


def read_submit_count(admin_collection: Collection) -> int:
    return admin_collection.find_one({'scope': 'app'})['submit_count']


def read_last_submit_datetime(admin_collection: Collection) -> None:
    return admin_collection.find_one({'scope': 'app'})['last_submit']


def reset_submit_count(admin_collection: Collection) -> None:
    update_submit_count(admin_collection, 0)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--reset_count', '-r',
                        help='Reset the listing submit count',
                        action='store_true')
    args = parser.parse_args()

    if args.reset_count:
        reset_submit_count(admin_collection)
        print(f'Reset submit count. Submit count: '
              f'{read_submit_count(admin_collection)}.')
