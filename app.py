import os
import peewee
import json
import pickle
import joblib
import pandas as pd
from flask import Flask, jsonify, request, Response, make_response
from peewee import Model, IntegerField, FloatField, TextField, IntegrityError, CompositeKey
from playhouse.shortcuts import model_to_dict
from playhouse.db_url import connect
from collections import OrderedDict

########################################
# Begin database code

DB = connect(os.environ.get('DATABASE_URL') or 'sqlite:///predictions.db')

class PriceForecast(Model):
    sku = TextField()
    time_key = IntegerField()
    pvp_is_competitorA = FloatField()
    pvp_is_competitorB = FloatField()
    pvp_is_competitorA_actual = FloatField(null=True) #added
    pvp_is_competitorB_actual = FloatField(null=True) #added

    class Meta:
        database = DB
        primary_key = CompositeKey('sku', 'time_key')

DB.create_tables([PriceForecast], safe=True)

#port = int(os.getenv("PORT", 5000))  # Default to 5000 if PORT isn't set activar para o deploy
#app.run(host="0.0.0.0", port=port) local não corre com app NameError: name 'app' is not defined
# End database code
########################################

########################################
# Begin webserver code

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

    pvp_is_competitorA = 12.0 + hash(sku) % 5
    pvp_is_competitorB = 16.0 + hash(sku) % 5

# Store forecasted prices in DB
    try:
        prediction, created = PriceForecast.get_or_create(
            sku=sku, time_key=time_key,
            defaults={"pvp_is_competitorA": 5.0, "pvp_is_competitorB": 9.0}#RETIRAR estes defaults
        )
    except IntegrityError:
        return jsonify({"error": "Database issue"}), 500

# Maintain field order explicitly on response
    response_data = OrderedDict([
        ("sku", sku),
        ("time_key", time_key),
        ("pvp_is_competitorA", pvp_is_competitorA),
        ("pvp_is_competitorB", pvp_is_competitorB)
    ])

    return Response(json.dumps(response_data, indent=4) + "\n", status=200, mimetype="application/json")
#jsonify(response_data)


@app.route('/actual_prices/', methods=['POST'])
def actual_prices():
    try:
        data = request.get_json()
        if not data:
            return make_response("Invalid JSON input", 422)
    except Exception:
        return make_response("Failed to parse JSON input.", 422)

    sku = data.get('sku')
    time_key = data.get('time_key')
    pvp_is_competitorA_actual = data.get('pvp_is_competitorA_actual')
    pvp_is_competitorB_actual = data.get('pvp_is_competitorB_actual')
    
    try:
        validate_data(sku, time_key)
    except ValueError as e:
        return make_response(str(e), 422)

    try:
        forecast = PriceForecast.get(PriceForecast.sku == sku, PriceForecast.time_key == time_key)
        forecast.pvp_is_competitorA_actual = pvp_is_competitorA_actual
        forecast.pvp_is_competitorB_actual = pvp_is_competitorB_actual
        forecast.save()
        return jsonify(model_to_dict(forecast))
    except PriceForecast.DoesNotExist:
        return make_response("Forecast with the specified SKU and time_key does not exist.", 422)

    return Response(json.dumps({
    "sku": prediction.sku,
    "time_key": prediction.time_key,
    "pvp_is_competitorA": prediction.pvp_is_competitorA,
    "pvp_is_competitorB": prediction.pvp_is_competitorB,
    "pvp_is_competitorA_actual": prediction.pvp_is_competitorA_actual,
    "pvp_is_competitorB_actual": prediction.pvp_is_competitorB_actual
}, indent=4) + "\n", status=200, mimetype="application/json")


# Validation function to check if SKU and time_key meet the required conditions
def validate_data(sku, time_key):
    if not sku or not isinstance(sku, str) or not sku.isdigit() or len(sku) != 4:
        raise ValueError("SKU must be exactly 4 digits, nnnn string format with "" before and after, and only contain numbers.")
    try:
        date = pd.to_datetime(str(time_key), format='%Y%m%d')
        if date <= pd.Timestamp('2024-10-31'):
            raise ValueError("time_key must be a date after 2024-10-31.")
    except ValueError:
        raise ValueError("time_key must be a valid date in YYYYMMDD format.")



@app.route('/list-db-contents', methods=['GET'])
def list_db_contents():
    return jsonify([model_to_dict(pred) for pred in PriceForecast.select()])


# Run Server
#if __name__ == "__main__":
#    app.run(host='0.0.0.0', debug=True, port=5000)

if __name__ == '__main__':
    try:
        app.run(host='0.0.0.0', debug=True, port=5000)
    except Exception as err:
        print(f"Failed to start application: {err}")

# End webserver code
######################################## 