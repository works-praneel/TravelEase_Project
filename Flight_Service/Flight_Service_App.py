from flask import Flask, request, jsonify
from flask_cors import CORS
import boto3
import os
from boto3.dynamodb.conditions import Key
from botocore.exceptions import ClientError

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})

# ==========================================================
# 🛑 NAYA: AWS DYNAMODB SETUP 🛑
# ==========================================================
FLIGHTS_TABLE_NAME = os.environ.get("FLIGHTS_TABLE_NAME", "TravelEase-Flights")
dynamodb = boto3.resource('dynamodb')
flights_table = dynamodb.Table(FLIGHTS_TABLE_NAME)

# --- API Endpoints ---
@app.route('/')
def home(): return "Flight Service (AWS) is running."
@app.route('/ping')
def ping(): return "OK", 200

@app.route('/api/flights', methods=['GET'])
def search_flights():
    flight_type = request.args.get('type')
    from_dest = request.args.get('from')
    to_dest = request.args.get('to')
    
    # 🛑 NAYA: 'date' parameter zaroori hai
    # flight_date = request.args.get('date') 
    # Abhi ke liye, hum route se search kar rahe hain

    if not all([flight_type, from_dest, to_dest]):
        return jsonify({"error": "Missing required query parameters"}), 400

    route_str = f"{from_dest}-{to_dest}"
    
    # --- DYNAMODB QUERY LOGIC ---
    # Humne table ko 'route' par query karne ke liye design kiya hai (GSI)
    try:
        response = flights_table.query(
            IndexName='route-index', # Yeh GSI hum Terraform mein banayenge
            KeyConditionExpression=Key('route').eq(route_str)
        )
        
        # Query ke baad, 'type' se filter karein
        results = [f for f in response.get('Items', []) if f['type'] == flight_type]
        
        # DynamoDB numbers ko Decimal() type mein return karta hai, JSON ke liye int/float mein convert karein
        # Yeh ek helper function se behtar ho sakta hai, but for simplicity:
        clean_results = []
        for f in results:
            f['price'] = int(f['price'])
            clean_results.append(f)
            
    except ClientError as e:
        print(f"DYNAMODB ERROR querying flights: {e}")
        return jsonify({"error": "Could not fetch flights."}), 500
    
    if not results: 
        print(f"No flights found for route: {route_str} and type: {flight_type}")
        
    return jsonify({"flights": clean_results})

# --- Main Execution ---
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5002)
