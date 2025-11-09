#
# FINAL FIXED VERSION - Payment_Service_App.py
#
from flask import Flask, request, jsonify
from flask_cors import CORS
import os
import uuid
from decimal import Decimal

# ---- Optional: Prometheus metrics setup ----
try:
    from prometheus_flask_exporter import PrometheusMetrics
    metrics_class = PrometheusMetrics
except ImportError:
    print("PrometheusMetrics not found. Using dummy metrics class.")
    class DummyMetrics:
        def __init__(self, app=None):
            if app:
                print("Dummy metrics attached.")
        def init_app(self, app):
            pass
    metrics_class = DummyMetrics

# ---- Flask App Initialization ----
app = Flask(__name__)
CORS(app)

# Initialize Prometheus metrics
metrics = metrics_class(app)

# ---- Health + Root Endpoints ----
@app.route('/')
def payment_home():
    return "Payment Service is up and ready to process payments!", 200

@app.route('/ping', methods=['GET'])
def ping():
    """Health check endpoint for ALB"""
    return jsonify({"message": "Payment Service is running!"}), 200

# ---- Main Payment API ----
@app.route('/api/payment', methods=['POST'])
def payment():
    """
    Mock payment processor for the TravelEase app.
    Validates card details strictly:
      - No alphabets allowed
      - Card must be 16 digits (spaces allowed in input)
    Accepts any valid 16-digit numeric card.
    """
    try:
        data = request.get_json()
        if not data:
            return jsonify({"message": "No input data provided"}), 400

        # Extract fields from frontend
        card_number = data.get('card_number', '').strip()
        amount = Decimal(str(data.get('amount', 0)))
        flight_id = data.get('flight_id')
        flight_details = data.get('flight_details')
        seat_number = data.get('seat_number')
        user_email = data.get('email')

        # Validate required fields
        if not all([flight_id, flight_details, seat_number, user_email, amount > 0]):
            return jsonify({"message": "Payment failed: Missing or invalid data from frontend."}), 400

        # Normalize and validate card number
        card_number_clean = card_number.replace(" ", "")
        if any(ch.isalpha() for ch in card_number_clean):
            return jsonify({"message": "Invalid card number. Alphabets are not allowed."}), 400
        if not card_number_clean.isdigit() or len(card_number_clean) != 16:
            return jsonify({"message": "Invalid card number. Must be exactly 16 digits."}), 400

        # All checks passed — approve payment
        transaction_id = f"TXN-{str(uuid.uuid4())[:8].upper()}"

        return jsonify({
            "message": "Payment Successful",
            "transaction_id": transaction_id,
            "flight_id": flight_id,
            "flight_details": flight_details,
            "seat_number": seat_number,
            "user_email": user_email,
            "amount_paid": amount
        }), 200

    except Exception as e:
        print(f"Error in /api/payment: {e}")
        return jsonify({
            "message": "Payment failed due to an internal error.",
            "error": str(e)
        }), 500



if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5003)