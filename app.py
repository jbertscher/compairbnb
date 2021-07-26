import json
from flask import Flask, jsonify, redirect, render_template, Response, request, url_for
import os
from pymongo import MongoClient
from trip import Trip
from typing import Tuple, Union

app = Flask(__name__)

mongodb_uri = os.environ['MONGODB_URI']
client = MongoClient(mongodb_uri)
db=client['compairbnb']


@app.route('/submit_url/<trip_id>', methods=['POST'])
def submit_url(trip_id: str) -> Tuple[str, int]:
    new_url = request.form.get('url')
    if new_url != '':
        Trip(trip_id, db).write_listing_from_url(new_url)
        return 'OK', 200
    else:
        return 'ERROR', 204

# TODO: Delete this eventually. Don't think this is necessary because user will be written on vote. If no vote, user won't be saved but that's fine.
@app.route('/add_voter/<trip_id>', methods=['POST'])
def submit_voter(trip_id: str) -> Tuple[str, int]:
    voter = request.form.get('voterName')
    if voter != '':
        # Add voter to DB
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
        elif post['action'] == 'update_data':
            if post['field'] == 'comments':
                trip.add_comments(post['listing_id'], post['value'])
            elif post['field'] == 'preferences':
                trip.add_vote(post['listing_id'], post['value']['user'], post['value']['points'])
        return 'OK', 200


@app.route('/<trip_id>')
def home(trip_id: str) -> str:
    # all_listings = Trip(trip_id, listing_collection).get_and_combine_all_listings()
    return render_template('home.html', trip_id=trip_id)


if __name__=='__main__':
    app.run()
