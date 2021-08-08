from datetime import datetime
from flask import Flask, jsonify, render_template, Response, request
import os
from pymongo import MongoClient
from trip import Trip
import compairbnb
from typing import Tuple, Union

app = Flask(__name__)

mongodb_uri = os.environ['MONGODB_URI']
client = MongoClient(mongodb_uri)
db = client['compairbnb']
admin_collection = db['admin']

SUBMIT_LIMIT = 30


@app.route('/submit_url/<trip_id>', methods=['POST'])
def submit_url(trip_id: str) -> Tuple[str, int]:
    last_submit_hours_ago = (
        datetime.now() -
        compairbnb.read_last_submit_datetime(admin_collection)
    ).total_seconds()/3600

    print(f'Last submit was {last_submit_hours_ago} hours ago.')

    if last_submit_hours_ago >= 24:
        compairbnb.reset_submit_count()
        print('Last submit was more than 24 hours ago. Number of submits '
              'reset.')
    else:
        remaining_submits = (SUBMIT_LIMIT -
                             compairbnb.read_submit_count(admin_collection))
        print('Last submit was less than 24 hours ago. Number of submits '
              f'left: {remaining_submits}.')

    if(compairbnb.read_submit_count(admin_collection) >= SUBMIT_LIMIT):
        print('Submit count exceeded. Will reset in 24 hour after last '
              'successful submit.')
        return 'OK', 200
    else:
        new_url = request.form.get('url')
        if new_url != '':
            Trip(trip_id, db).write_listing_from_url(new_url)
            compairbnb.increment_submit_count(admin_collection)
            return 'OK', 200
        else:
            return 'ERROR', 204


@app.route('/api/<trip_id>', methods=['GET', 'POST'])
def api(trip_id: str) -> Union[Response, Tuple[str, int]]:
    trip = Trip(trip_id, db)
    # GET request
    if request.method == 'GET':
        response = trip.get_and_combine_all_listings()
        return jsonify(response)  # serialize and use JSON headers
    # POST request
    if request.method == 'POST':
        post = request.get_json()
        if post['action'] == 'delete_listing':
            trip.delete_listing(post['listing_id'])
        elif post['action'] == 'delete_user':
            trip.delete_voter(post['user'])
        elif post['action'] == 'update_data':
            if post['field'] == 'comments':
                trip.add_comments(post['listing_id'], post['value'])
            elif post['field'] == 'preferences':
                trip.add_vote(post['listing_id'], post['value']['user'],
                              post['value']['points'])
        return 'OK', 200


@app.route('/<trip_id>')
def home(trip_id: str) -> str:
    return render_template('home.html', trip_id=trip_id)


if __name__ == '__main__':
    app.run()
