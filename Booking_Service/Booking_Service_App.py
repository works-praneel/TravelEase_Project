from flask import Flask, request, jsonify
from flask_cors import CORS
import os
import uuid
import boto3
from decimal import Decimal

app = Flask(__name__)
CORS(app)

# Connect to DynamoDB
dynamodb = boto3.resource('dynamodb', region_name='eu-north-1')
table_name = 'SmartTripsDB'
table = dynamodb.Table(table_name)

@app.route('/ping', methods=['GET'])
def ping():
    return jsonify({"message": "Booking Service is running!"}), 200

@app.route('/book', methods=['POST'])
def book_flight():
    try:
        data = request.get_json()
        if not data:
            return jsonify({"message": "No input data provided"}), 400

        flight_id = data.get('flight_id')
        seat_number = data.get('seat_number')
        user_email = data.get('user_email')
        flight_details = data.get('flight_details') or data.get('flight')
        amount_paid = data.get('amount_paid') or data.get('amount') or data.get('price')
        transaction_id = data.get('transaction_id', f"TXN-{str(uuid.uuid4())[:8].upper()}")

        if not all([flight_id, seat_number, user_email, flight_details, amount_paid]):
            print("❌ Missing fields:", data)
            return jsonify({"message": "Missing required booking information"}), 400

        booking_reference = f"BK-{str(uuid.uuid4())[:6].upper()}"
        print(f"✅ Booking confirmed | {user_email} | {flight_id} | Seat {seat_number}")

        return jsonify({
            "message": "Booking Confirmed!",
            "booking_reference": booking_reference,
            "flight_id": flight_id,
            "seat_number": seat_number,
            "user_email": user_email,
            "amount_paid": amount_paid,
            "transaction_id": transaction_id,
            "email_status": "Sent"
        }), 200

    except Exception as e:
        print(f"Error in /book: {e}")
        return jsonify({"message": "Booking failed due to an internal error.", "error": str(e)}), 500


@app.route('/cancel', methods=['POST'])
def cancel_booking():
    return jsonify({"message": "Cancellation feature coming soon."}), 200


@app.route('/api/get_seats', methods=['GET'])
def get_booked_seats():
    flight_id = request.args.get('flight_id')
    return jsonify({"flight_id": flight_id, "booked_seats": []}), 200


@app.route('/smart-trip', methods=['POST'])
def get_smart_trip_recommendations():
    try:
        data = request.get_json(force=True, silent=True)
        destination_code = data.get("destination_code") or data.get("to", "").upper()
        if not destination_code:
            return jsonify({"message": "Missing destination code"}), 400

        print(f"Fetching smart trips for destination: {destination_code}")

        response = table.scan()
        all_items = response.get('Items', [])

        filtered = [
            item for item in all_items
            if item.get('destination_code', '').upper() == destination_code
        ]

        if not filtered:
            print(f"No smart trips found for {destination_code}")
            return jsonify({"recommendations": []}), 200

        # Clean up Decimal types for JSON
        for item in filtered:
            for key, value in item.items():
                if isinstance(value, Decimal):
                    item[key] = float(value)

        print(f"✅ Found {len(filtered)} smart trip options for {destination_code}")
        return jsonify({"recommendations": filtered}), 200

    except Exception as e:
        print(f"Error in /smart-trip: {e}")
        return jsonify({"message": "Error fetching smart trip recommendations", "error": str(e)}), 500


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(debug=True, host='0.0.0.0', port=port)
