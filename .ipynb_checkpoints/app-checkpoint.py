#!pip install peewee
import os
import peewee
import json
import pickle
import joblib
import pandas as pd
from flask import Flask, jsonify, request, Response
from peewee import Model, IntegerField, FloatField, TextField, IntegrityError, CompositeKey
from playhouse.shortcuts import model_to_dict
from playhouse.db_url import connect
from collections import OrderedDict

########################################
# Begin database stuff

DB = connect(os.environ.get('DATABASE_URL') or 'sqlite:///predictions.db')

class PriceForecast(Model):
    sku = TextField()
    time_key = IntegerField()
    pvp_is_competitorA = FloatField()
    pvp_is_competitorB = FloatField()

    class Meta:
        database = DB
        primary_key = CompositeKey('sku', 'time_key')

DB.create_tables([PriceForecast], safe=True)

# End database stuff
########################################

########################################
# Begin webserver stuff

app = Flask(__name__)

@app.errorhandler(422)
def handle_unprocessable_entity(error):
    return Response(str(error), status=422, content_type='text/plain')

@app.route('/forecast_prices/', methods=['POST'])
def forecast_prices():
    try:
        data = request.get_json()
        if not data:
            return Response("Invalid JSON input", status=422, content_type='text/plain')
    except Exception:
        return Response("Failed to parse JSON input.", status=422, content_type='text/plain')

    sku = data.get('sku')
    time_key = data.get('time_key')
    
    try:
        validate_data(sku, time_key)
    except ValueError as e:
        return Response(str(e), status=422, content_type='text/plain')

    pvp_is_competitorA = 10.0 + hash(sku) % 5
    pvp_is_competitorB = 15.0 + hash(sku) % 5

    response_data = OrderedDict([
        ("sku", sku),
        ("time_key", time_key),
        ("pvp_is_competitorA", pvp_is_competitorA),
        ("pvp_is_competitorB", pvp_is_competitorB)
    ])

    return jsonify(response_data)

# Validation function to check if SKU and time_key meet the required conditions
def validate_data(sku, time_key):
    if not sku or not isinstance(sku, str) or not sku.isdigit() or len(sku) != 4:
        raise ValueError("SKU must be exactly 4 digits and only contain numbers.")
    try:
        date = pd.to_datetime(str(time_key), format='%Y%m%d')
        if date <= pd.Timestamp('2025-01-01'):
            raise ValueError("time_key must be a date after 2025-01-01.")
    except ValueError:
        raise ValueError("time_key must be a valid date in YYYYMMDD format.")

if __name__ == '__main__':
    try:
        app.run(host='0.0.0.0', debug=True, port=5000)
    except Exception as err:
        print(f"Failed to start application: {err}")

# End webserver stuff
######################################## 