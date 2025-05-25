import os
import json
import pickle
import joblib
import pandas as pd
from flask import Flask, jsonify, request, Response
from peewee import Model, IntegerField, FloatField, TextField, IntegrityError, SQL
from playhouse.shortcuts import model_to_dict
from playhouse.db_url import connect
from collections import OrderedDict

# Database Setup
DB = connect(os.environ.get('DATABASE_URL') or 'sqlite:///prices.db')

port = int(os.getenv("PORT", 5000))  # Default to 5000 if PORT isn't set
app.run(host="0.0.0.0", port=port)

class PricePrediction(Model):
    sku = TextField()
    time_key = IntegerField()
    pvp_is_competitorA = FloatField(default=5.0)  # Test only, default price
    pvp_is_competitorB = FloatField(default=9.0)  # Test only, default price
    pvp_is_competitorA_actual = FloatField(null=True)
    pvp_is_competitorB_actual = FloatField(null=True)

    class Meta:
        database = DB
        constraints = [SQL("UNIQUE(sku, time_key)")]
        primary_key = False

DB.create_tables([PricePrediction], safe=True)

# Flask App Setup
app = Flask(__name__)

@app.route('/forecast_prices/', methods=['POST'])
def forecast_prices():
    try:
        request_data = request.get_json()
    except Exception:
        return jsonify({"error 410": "Invalid JSON format"}), 410
    sku = request_data.get("sku")
    time_key = request_data.get("time_key")

    # Ensure required fields are present
    if sku is None or time_key is None:
        return jsonify({"error 422": "Must insert `sku` and `time_key`"}), 422
    
    # Validate columns
    if not sku or not isinstance(time_key, int):
        return jsonify({"error 422": "Must insert 'SKU' and 'time_key'"}), 422

    # Validate SKU: Must be digits only and exactly 4 digits long
    if not isinstance(sku, str) or not sku.isdigit() or len(sku) != 4:
        return jsonify({"error 422": "SKU must be a 4-digit string, containing only digits"}), 422
    
    # Validate time_key lengh
    if not isinstance(time_key, int) or not len(time_key) != 8:
        return jsonify({"error 422": "time_key must be an integer in yyyymmdd format"}), 422

    #try:
     #   datetime.datetime.strptime(time_key, "%Y%m%d")
    #except ValueError:
     #   return jsonify({"error 422": "time_key is not a valid calendar date"}), 422   

    # Store forecasted prices in DB
    try:
        prediction, created = PricePrediction.get_or_create(
            sku=sku, time_key=time_key,
            defaults={"pvp_is_competitorA": 5.0, "pvp_is_competitorB": 9.0}
        )
    except IntegrityError:
        return jsonify({"error": "Database issue"}), 500

    # Maintain field order explicitly on different lines
    response_data = OrderedDict([
    ("sku", prediction.sku),
    ("time_key", prediction.time_key),
    ("pvp_is_competitorA", prediction.pvp_is_competitorA),
    ("pvp_is_competitorB", prediction.pvp_is_competitorB)
])

    return Response(json.dumps(response_data, indent=4) + "\n", status=200, mimetype="application/json")

@app.route('/actual_prices/', methods=['POST'])
def actual_prices():
    request_data = request.get_json()
    sku = request_data.get("sku")
    time_key = request_data.get("time_key")
    pvp_is_competitorA_actual = request_data.get("pvp_is_competitorA_actual")
    pvp_is_competitorB_actual = request_data.get("pvp_is_competitorB_actual")

    if not sku or not isinstance(time_key, int) or pvp_is_competitorA_actual is None or pvp_is_competitorB_actual is None:
        return jsonify({"error": "Invalid input format"}), 422

    try:
        prediction = PricePrediction.get(PricePrediction.sku == sku, PricePrediction.time_key == time_key)
        prediction.pvp_is_competitorA_actual = pvp_is_competitorA_actual
        prediction.pvp_is_competitorB_actual = pvp_is_competitorB_actual
        prediction.save()
    except PricePrediction.DoesNotExist:
        return jsonify({"error": "Product-date pair not found"}), 422

    return Response(json.dumps({
    "sku": prediction.sku,
    "time_key": prediction.time_key,
    "pvp_is_competitorA": prediction.pvp_is_competitorA,
    "pvp_is_competitorB": prediction.pvp_is_competitorB,
    "pvp_is_competitorA_actual": prediction.pvp_is_competitorA_actual,
    "pvp_is_competitorB_actual": prediction.pvp_is_competitorB_actual
}, indent=4) + "\n", status=200, mimetype="application/json")


@app.route('/list-db-contents', methods=['GET'])
def list_db_contents():
    return jsonify([model_to_dict(pred) for pred in PricePrediction.select()])


# Run Server
if __name__ == "__main__":
    app.run(host='0.0.0.0', debug=True, port=5000)
