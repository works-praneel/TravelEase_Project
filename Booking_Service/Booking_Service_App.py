from flask import Flask, request, jsonify, abort
from flask_cors import CORS
import os, uuid, logging
import boto3
from decimal import Decimal
from email_sender_gmail import send_confirmation_email, send_cancellation_email

app = Flask(__name__)
CORS(app)
logging.basicConfig(level=logging.INFO, format='[%(asctime)s] %(levelname)s: %(message)s')

# DynamoDB (kept for smart-trip usage). Adjust region if needed.
dynamodb = boto3.resource('dynamodb', region_name='eu-north-1')
table_name = os.getenv("SMART_TRIPS_TABLE", "SmartTripsDB")
table = dynamodb.Table(table_name)


@app.route("/ping", methods=["GET"])
def ping():
    return jsonify({"message": "Booking Service is running!"}), 200


@app.route("/book", methods=["POST"])
def book_flight():
    try:
        data = request.get_json()
        if not data:
            return jsonify({"message": "No input data provided"}), 400

        flight_id = data.get("flight_id")
        seat_number = data.get("seat_number")
        user_email = data.get("user_email")
        flight_details = data.get("flight_details") or data.get("flight")
        amount_paid = data.get("amount_paid") or data.get("amount") or data.get("price")
        transaction_id = data.get("transaction_id", f"TXN-{uuid.uuid4().hex[:8].upper()}")

        if not all([flight_id, seat_number, user_email, flight_details, amount_paid]):
            return jsonify({"message": "Missing required booking information"}), 400

        booking_reference = f"BK-{uuid.uuid4().hex[:6].upper()}"

        # attempt send email but do not fail booking on email issues
        booking_info = {
            "booking_reference": booking_reference,
            "flight_id": flight_id,
            "amount_paid": amount_paid,
            "transaction_id": transaction_id
        }

        email_sent = send_confirmation_email(user_email, booking_info)

        # internal log only
        if not email_sent:
            logging.warning(f"Confirmation email failed for booking {booking_reference}")

        return jsonify({
            "message": "Booking Confirmed!",
            "booking_reference": booking_reference,
            "flight_id": flight_id,
            "seat_number": seat_number,
            "user_email": user_email,
            "amount_paid": amount_paid,
            "transaction_id": transaction_id,
            "email_status": "Sent" if email_sent else "Failed"
        }), 200

    except Exception as e:
        logging.error(f"Booking error: {e}")
        return jsonify({"message": "Booking failed", "error": str(e)}), 500


@app.route("/cancel", methods=["POST"])
def cancel_booking():
    """
    Expected JSON:
      {
        "booking_reference": "BK-xxxxxx",
        "user_email": "user@example.com",
        "flight": "Flight name or details",
        "price": 1234.0
      }
    This endpoint will process cancellation (stateless here) and send cancellation email.
    """
    try:
        data = request.get_json()
        if not data:
            return jsonify({"message": "No input data provided"}), 400

        booking_reference = data.get("booking_reference")
        user_email = data.get("user_email")
        flight = data.get("flight", "")
        price = data.get("price")

        if not booking_reference or not user_email or price is None:
            return jsonify({"message": "Missing required cancellation fields"}), 400

        # simple refund calc: 55% (as earlier)
        try:
            refund_amount = round(float(price) * 0.55, 2)
        except Exception:
            refund_amount = 0.0

        booking_details = {
            "booking_reference": booking_reference,
            "flight": flight,
            "price": price
        }

        # send cancellation email, but do not fail the API if email fails
        email_sent = send_cancellation_email(user_email, booking_details, refund_amount)
        if not email_sent:
            logging.warning(f"Cancellation email failed for booking {booking_reference}")

        return jsonify({
            "message": "Cancellation processed",
            "booking_reference": booking_reference,
            "refund_amount": refund_amount,
            "email_status": "Sent" if email_sent else "Failed"
        }), 200

    except Exception as e:
        logging.error(f"Cancellation error: {e}")
        return jsonify({"message": "Cancellation failed", "error": str(e)}), 500


@app.route("/api/get_seats", methods=["GET"])
def get_booked_seats():
    flight_id = request.args.get("flight_id")
    return jsonify({"flight_id": flight_id, "booked_seats": []}), 200


@app.route("/smart-trip", methods=["POST"])
def get_smart_trip_recommendations():
    try:
        data = request.get_json(force=True, silent=True) or {}
        destination_code = (data.get("destination_code") or data.get("to") or "").upper()
        if not destination_code:
            return jsonify({"message": "Missing destination code"}), 400

        response = table.scan()
        all_items = response.get("Items", [])

        filtered = [
            item for item in all_items
            if item.get("destination_code", "").upper() == destination_code
        ]

        # convert Decimal to float
        for item in filtered:
            for k, v in list(item.items()):
                if isinstance(v, Decimal):
                    item[k] = float(v)

        return jsonify({"recommendations": filtered}), 200

    except Exception as e:
        logging.error(f"Smart-trip error: {e}")
        return jsonify({"message": "Error fetching smart trip recommendations", "error": str(e)}), 500


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)
