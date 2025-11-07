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
    Approves card numbers starting with '4242' for testing.
    """
    try:
        data = request.get_json()
        if not data:
            return jsonify({"message": "No input data provided"}), 400

        # Extract fields from frontend
        card_number = data.get('card_number', '')
        amount = Decimal(str(data.get('amount', 0)))
        flight_id = data.get('flight_id')
        flight_details = data.get('flight_details')
        seat_number = data.get('seat_number')
        user_email = data.get('email')

        # Validate all essential fields
        if not all([flight_id, flight_details, seat_number, user_email, amount > 0, len(card_number) >= 16]):
            return jsonify({"message": "Payment failed: Invalid or missing data from frontend."}), 400

        transaction_id = f"TXN-{str(uuid.uuid4())[:8].upper()}"

        # Mock approval logic
        if card_number.startswith("4242"):
            return jsonify({
                "message": "Payment Successful",
                "transaction_id": transaction_id,
                "flight_id": flight_id,
                "flight_details": flight_details,
                "seat_number": seat_number,
                "user_email": user_email,
                "amount_paid": amount
            }), 200
        else:
            return jsonify({
                "message": "Payment Failed. Your bank declined the transaction."
            }), 402

    except Exception as e:
        print(f"Error in /api/payment: {e}")
        return jsonify({
            "message": "Payment failed due to an internal error.",
            "error": str(e)
        }), 500


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5003)
