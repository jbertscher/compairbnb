from compairbnb import *
from flask import Flask, jsonify, redirect, render_template, request, url_for

app = Flask(__name__)

@app.route('/submit_url', methods=['POST'])
def submit_url():
    new_url = request.form.get('url')
    write_listing_from_url(new_url)
    return redirect(url_for('home'))

@app.route('/api', methods=['GET', 'POST'])
def api():
    # GET request
    if request.method == 'GET':
        response = combine_all_listings(LISTINGS_DIR).to_json()
        return jsonify(response)  # serialize and use JSON headers
    # POST request
    if request.method == 'POST':
        print(request.get_json())  # parse as JSON
        return 'Success', 200

@app.route('/')
def home():
    all_listings = combine_all_listings(LISTINGS_DIR)
    # all_listings_html = all_listings.to_html(classes='listings')
    all_listings_html = create_html_table(all_listings) 

    return render_template('home.html',
        listings_data=all_listings.to_json,
        listings_table=all_listings_html, 
        titles=all_listings.columns.values)

print('http://127.0.0.1:5000/')
