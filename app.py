!pip install peewee
import os
import json
import pickle
import joblib
import pandas as pd
from flask import Flask, jsonify, request, abort
from peewee import Model, IntegerField, FloatField, TextField, IntegrityError
from playhouse.shortcuts import model_to_dict
from playhouse.db_url import connect

########################################
# Begin database stuff

# The connect function checks if there is a DATABASE_URL env var.
# If it exists, it uses it to connect to a remote postgres db.
# Otherwise, it connects to a local sqlite db stored in predictions.db.
DB = connect(os.environ.get('DATABASE_URL') or 'sqlite:///predictions.db')

class PriceForecast(Model):
    sku = TextField()
    time_key = IntegerField()
    pvp_is_competitorA = FloatField()
    pvp_is_competitorB = FloatField()
    pvp_is_competitorA_actual = FloatField(null=True)
    pvp_is_competitorB_actual = FloatField(null=True)
    
    class Meta:
        database = DB

DB.create_tables([PriceForecast], safe=True)

# End database stuff
########################################

########################################
# Begin webserver stuff

app = Flask(__name__)

@app.route('/forecast_prices/', methods=['POST'])
def forecast_prices():
    # Get data from the request
    data = request.get_json()
    sku = data.get('sku')
    time_key = data.get('time_key')
    
    # Validate the data
    validate_data(sku, time_key)

    # Mockup for predicted prices
    pvp_is_competitorA = 10.0 + hash(sku) % 5  # Placeholder logic for predictions
    pvp_is_competitorB = 15.0 + hash(sku) % 5
    
    # Create a new forecast and save it
    forecast = PriceForecast(
        sku=sku,
        time_key=time_key,
        pvp_is_competitorA=pvp_is_competitorA,
        pvp_is_competitorB=pvp_is_competitorB
    )
    try:
        forecast.save()
        return jsonify(model_to_dict(forecast))
    except IntegrityError:
        return jsonify({'error': 'Forecast with the same SKU and time_key already exists.'}), 422

@app.route('/actual_prices/', methods=['POST'])
def actual_prices():
    # Get data from the request
    data = request.get_json()
    sku = data.get('sku')
    time_key = data.get('time_key')
    pvp_is_competitorA_actual = data.get('pvp_is_competitorA_actual')
    pvp_is_competitorB_actual = data.get('pvp_is_competitorB_actual')

    # Validate the data
    validate_data(sku, time_key)

    try:
        forecast = PriceForecast.get(PriceForecast.sku == sku, PriceForecast.time_key == time_key)
        forecast.pvp_is_competitorA_actual = pvp_is_competitorA_actual
        forecast.pvp_is_competitorB_actual = pvp_is_competitorB_actual
        forecast.save()
        return jsonify(model_to_dict(forecast))
    except PriceForecast.DoesNotExist:
        return jsonify({'error': 'Forecast with the specified SKU and time_key does not exist.'}), 422

# Validation function to check if SKU and time_key meet the required conditions
def validate_data(sku, time_key):
    # Check if SKU is numeric and 4 digits
    if not sku.isdigit() or len(sku) != 4:
        abort(422, "SKU must be exactly 4 digits and only contain numbers.")
        
    # Check if time_key represents a valid date after 2025-01-01
    try:
        date = pd.to_datetime(str(time_key), format='%Y%m%d')
        if date <= pd.Timestamp('2025-01-01'):
            abort(422, "time_key must be a date after 2025-01-01.")
    except ValueError:
        abort(422, "time_key must be a valid date in YYYYMMDD format.")

if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True, port=5000)

# End webserver stuff
######################################## 