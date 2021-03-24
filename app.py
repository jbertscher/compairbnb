from compairbnb import *
from flask import Flask, jsonify, redirect, render_template, request, url_for

app = Flask(__name__)


@app.route('/submit_url/<trip_id>', methods=['POST'])
def submit_url(trip_id):
    new_url = request.form.get('url')
    if new_url != '':
        write_listing_from_url(new_url, trip_id)
    else:
        print('No URL given')
    return redirect(url_for('home', trip_id=trip_id))


@app.route('/api/<trip_id>', methods=['GET', 'POST'])
def api(trip_id):
    # GET request
    if request.method == 'GET':
        response = combine_all_listings(trip_id).to_json(orient='records')
        return jsonify(response)  # serialize and use JSON headers
    # POST request
    if request.method == 'POST':
        post = request.get_json()
        if post['action'] == 'delete_listing':
            delete_listing(post['listing_id'], trip_id)
        return 'OK', 200


@app.route('/<trip_id>')
def home(trip_id):
    all_listings = combine_all_listings(trip_id)
    return render_template('home.html', trip_id=trip_id)


if __name__=='__main__':
    app.run()
