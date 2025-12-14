from flask import Flask, request, jsonify
from flask_cors import CORS
import os
import uuid
import logging
import boto3
from decimal import Decimal
from email_sender_gmail import (
    send_confirmation_email,
    send_cancellation_email
)

# -------------------------------
# App & Logging
# -------------------------------
app = Flask(__name__)
CORS(app)

logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] %(levelname)s: %(message)s'
)

# -------------------------------
# DynamoDB Configuration
# -------------------------------
AWS_REGION = "eu-north-1"
BOOKINGS_TABLE = os.getenv("BOOKINGS_TABLE", "BookingsDB")
SMART_TRIPS_TABLE = os.getenv("SMART_TRIPS_TABLE", "SmartTripsDB")

dynamodb = boto3.resource("dynamodb", region_name=AWS_REGION)
bookings_table = dynamodb.Table(BOOKINGS_TABLE)
smart_trips_table = dynamodb.Table(SMART_TRIPS_TABLE)

# -------------------------------
# Health Check
# -------------------------------
@app.route("/ping", methods=["GET"])
def ping():
    return jsonify({"message": "Booking Service is running!"}), 200

# -------------------------------
# BOOK FLIGHT
# -------------------------------
@app.route("/book", methods=["POST"])
def book_flight():
    try:
        data = request.get_json(force=True, silent=True) or {}

        flight_id = data.get("flight_id")
        seat_number = data.get("seat_number")
        user_email = data.get("user_email")
        flight_details = data.get("flight_details") or data.get("flight")
        amount_paid = data.get("amount_paid") or data.get("amount") or data.get("price")
        transaction_id = data.get(
            "transaction_id",
            f"TXN-{uuid.uuid4().hex[:8].upper()}"
        )

        if not all([flight_id, seat_number, user_email, flight_details, amount_paid]):
            return jsonify({"message": "Missing required booking information"}), 400

        booking_reference = f"BK-{uuid.uuid4().hex[:6].upper()}"

        # -------------------------------
        # Persist Booking in DynamoDB
        # -------------------------------
        bookings_table.put_item(
            Item={
                "booking_reference": booking_reference,
                "flight_id": flight_id,
                "flight_details": flight_details,
                "seat_number": seat_number,
                "user_email": user_email,
                "amount_paid": Decimal(str(amount_paid)),
                "transaction_id": transaction_id
            }
        )

        # -------------------------------
        # Send Confirmation Email
        # -------------------------------
        booking_info = {
            "booking_reference": booking_reference,
            "flight_id": flight_id,
            "amount_paid": amount_paid,
            "transaction_id": transaction_id
        }

        email_sent = send_confirmation_email(user_email, booking_info)

        if not email_sent:
            logging.warning(
                f"Confirmation email failed for booking {booking_reference}"
            )

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
        return jsonify({"message": "Booking failed"}), 500

# -------------------------------
# CANCEL BOOKING (FIXED)
# -------------------------------
@app.route("/cancel", methods=["POST"])
def cancel_booking():
    try:
        data = request.get_json(force=True, silent=True) or {}

        booking_reference = data.get("booking_reference")
        user_email = data.get("user_email")

        if not booking_reference or not user_email:
            return jsonify({"message": "Missing required cancellation fields"}), 400

        # -------------------------------
        # Fetch Booking Details
        # -------------------------------
        response = bookings_table.get_item(
            Key={"booking_reference": booking_reference}
        )

        booking = response.get("Item")
        if not booking:
            return jsonify({"message": "Booking not found"}), 404

        price = float(booking.get("amount_paid", 0))
        refund_amount = round(price * 0.55, 2)

        booking_details = {
            "booking_reference": booking_reference,
            "flight": booking.get("flight_details"),
            "price": price
        }

        # -------------------------------
        # Send Cancellation Email
        # -------------------------------
        email_sent = send_cancellation_email(
            user_email,
            booking_details,
            refund_amount
        )

        if not email_sent:
            logging.warning(
                f"Cancellation email failed for booking {booking_reference}"
            )

        # -------------------------------
        # Delete Booking (optional but logical)
        # -------------------------------
        bookings_table.delete_item(
            Key={"booking_reference": booking_reference}
        )

        return jsonify({
            "message": "Cancellation processed",
            "booking_reference": booking_reference,
            "refund_amount": refund_amount,
            "email_status": "Sent" if email_sent else "Failed"
        }), 200

    except Exception as e:
        logging.error(f"Cancellation error: {e}")
        return jsonify({"message": "Cancellation failed"}), 500

# -------------------------------
# GET BOOKED SEATS (Stub)
# -------------------------------
@app.route("/api/get_seats", methods=["GET"])
def get_booked_seats():
    flight_id = request.args.get("flight_id")
    return jsonify({
        "flight_id": flight_id,
        "booked_seats": []
    }), 200

# -------------------------------
# SMART TRIP RECOMMENDATIONS
# -------------------------------
@app.route("/smart-trip", methods=["POST"])
def get_smart_trip_recommendations():
    try:
        data = request.get_json(force=True, silent=True) or {}
        destination_code = (data.get("destination_code") or data.get("to") or "").upper()

        if not destination_code:
            return jsonify({"message": "Missing destination code"}), 400

        response = smart_trips_table.scan()
        items = response.get("Items", [])

        filtered = [
            item for item in items
            if item.get("destination_code", "").upper() == destination_code
        ]

        for item in filtered:
            for k, v in item.items():
                if isinstance(v, Decimal):
                    item[k] = float(v)

        return jsonify({"recommendations": filtered}), 200

    except Exception as e:
        logging.error(f"Smart-trip error: {e}")
        return jsonify({"message": "Error fetching smart trip recommendations"}), 500

# -------------------------------
# Main
# -------------------------------
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)
