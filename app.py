from flask import Flask, jsonify, redirect, render_template, request, url_for
import os
from pymongo import MongoClient
from trip import Listing, Trip

app = Flask(__name__)

mongodb_uri = os.environ['MONGODB_URI']
client = MongoClient(mongodb_uri)
db=client['compairbnb']
listing_collection = db['listings']


@app.route('/submit_url/<trip_id>', methods=['POST'])
def submit_url(trip_id):
    new_url = request.form.get('url')
    if new_url != '':
        Trip(trip_id, listing_collection).write_listing_from_url(new_url)
        return 'OK', 200
    else:
        return 'ERROR', 204


@app.route('/api/<trip_id>', methods=['GET', 'POST'])
def api(trip_id):
    trip = Trip(trip_id, listing_collection)
    # GET request
    if request.method == 'GET':
        response = trip.get_and_combine_all_listings()
        return jsonify(response)  # serialize and use JSON headers
    # POST request
    if request.method == 'POST':
        post = request.get_json()
        if post['action'] == 'delete_listing':
            trip.delete_listing(post['listing_id'])
        return 'OK', 200


@app.route('/<trip_id>')
def home(trip_id):
    # all_listings = Trip(trip_id, listing_collection).get_and_combine_all_listings()
    return render_template('home.html', trip_id=trip_id)


if __name__=='__main__':
    app.run()
