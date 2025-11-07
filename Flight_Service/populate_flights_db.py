import boto3
import random
from itertools import permutations
import datetime
import uuid

# ==========================================================
# 🛑 NOTE: Is script ko manually chalayein 🛑
#
# 1. Apne local machine par AWS credentials setup karein
#    (e.g., via `aws configure`)
# 2. `pip install boto3` karein
# 3. `python populate_flights_db.py` chalayein
# ==========================================================

FLIGHTS_TABLE_NAME = "TravelEase-Flights" # Yeh naam Terraform file se match hona chahiye
dynamodb = boto3.resource('dynamodb')
flights_table = dynamodb.Table(FLIGHTS_TABLE_NAME)

# --- Data for Flight Generation (Aapke original code se) ---
DOMESTIC_AIRLINES = ["IndiGo", "Vistara", "Air India", "SpiceJet", "Akasa Air", "AirAsia India"]
INTERNATIONAL_AIRLINES = {
    "HKT": ["Thai Airways", "IndiGo", "SpiceJet", "Go First"],
    "SUB": ["Garuda Indonesia", "Batik Air", "Singapore Airlines", "Malaysia Airlines"],
    "NRT": ["Japan Airlines", "ANA", "Air India", "Vistara", "Singapore Airlines"],
    "HND": ["Japan Airlines", "ANA", "Vistara"],
    "DXB": ["Emirates", "Flydubai", "Air India Express", "IndiGo", "Vistara", "SpiceJet"],
    "SYD": ["Qantas", "Air India", "Singapore Airlines", "Thai Airways"],
    "MEL": ["Qantas", "Air India", "Malaysia Airlines", "Cathay Pacific"],
    "AKL": ["Air New Zealand", "Singapore Airlines", "Qantas", "Emirates", "Malaysia Airlines"]
}
DOMESTIC_HUBS = ["DEL", "BOM", "CCU", "MAA", "HYD", "GOI"]
INTERNATIONAL_HUBS = ["HKT", "SUB", "NRT", "HND", "DXB", "SYD", "MEL", "AKL"]

GENERIC_ROUTE_PROFILES = {
    "domestic_short": (4000, 100),
    "domestic_medium": (6000, 140),
    "international_short": (18000, 240),
    "international_medium": (25000, 420),
    "international_long": (45000, 750),
    "international_xl": (65000, 950)
}

def generate_flights(flight_type, route_key, num_flights=10):
    flights = []
    origin, dest = route_key.split('-')
    
    profile_key = "domestic_medium"
    if flight_type == "domestic":
        if {origin, dest} in [{"BOM", "HYD"}, {"BOM", "GOI"}, {"MAA", "HYD"}]:
            profile_key = "domestic_short"
    else:
        intl_hub = dest if dest in INTERNATIONAL_HUBS else origin
        if intl_hub in ["DXB"]: profile_key = "international_short"
        elif intl_hub in ["HKT", "SUB"]: profile_key = "international_medium"
        elif intl_hub in ["SYD", "MEL", "NRT", "HND"]: profile_key = "international_long"
        elif intl_hub in ["AKL"]: profile_key = "international_xl"

    base_price, base_duration = GENERIC_ROUTE_PROFILES[profile_key]

    for _ in range(num_flights):
        if flight_type == "domestic":
            airline = random.choice(DOMESTIC_AIRLINES)
        else:
            intl_hub = dest if dest in INTERNATIONAL_HUBS else origin
            airline = random.choice(INTERNATIONAL_AIRLINES.get(intl_hub, ["Intl. Airline"]))
        
        flight_prefix = airline.split(' ')[0][:2].upper()
        flight_number = f"{flight_prefix}-{random.randint(100, 9999)}"

        price_variation = random.randint(-2000, 2000)
        duration_variation = random.randint(-30, 30)
        
        final_price = base_price + price_variation
        final_duration_min = base_duration + duration_variation
        hours, minutes = divmod(final_duration_min, 60)

        departure_hour = random.randint(0, 23)
        departure_minute = random.choice([0, 15, 30, 45])
        departure_time = datetime.datetime(2025, 1, 1, departure_hour, departure_minute)
        arrival_time = departure_time + datetime.timedelta(minutes=final_duration_min)
        
        flight = {
            "flight_id": str(uuid.uuid4()), # Primary Key
            "type": flight_type,
            "name": airline,
            "flightNumber": flight_number,
            "route": f"{origin}-{dest}", # GSI Partition Key
            "price": final_price,
            "duration": f"{hours}h {minutes}m",
            "departureTime": departure_time.strftime("%H:%M"),
            "arrivalTime": arrival_time.strftime("%H:%M")
            # Note: Asli system mein yahan 'date' bhi hogi
        }
        flights.append(flight)
    return flights

def main():
    ALL_FLIGHTS = []
    print("Generating flight data...")
    # 1. Domestic
    for origin, dest in permutations(DOMESTIC_HUBS, 2):
        ALL_FLIGHTS.extend(generate_flights("domestic", f"{origin}-{dest}", 10))
    # 2. International (To)
    for origin in DOMESTIC_HUBS:
        for dest in INTERNATIONAL_HUBS:
            ALL_FLIGHTS.extend(generate_flights("international", f"{origin}-{dest}", 10))
    # 3. International (From)
    for origin in INTERNATIONAL_HUBS:
        for dest in DOMESTIC_HUBS:
            ALL_FLIGHTS.extend(generate_flights("international", f"{origin}-{dest}", 10))
            
    print(f"Generated {len(ALL_FLIGHTS)} flights. Uploading to DynamoDB...")

    # DynamoDB Batch Writer ka istemal karein (efficient)
    with flights_table.batch_writer() as batch:
        for flight in ALL_FLIGHTS:
            # Price ko int se Decimal mein convert karein (DynamoDB requirement)
            # Lekin boto3 v2.3+ ints ko handle kar leta hai. Hum ise simple rakhenge.
            # flight['price'] = Decimal(str(flight['price'])) 
            batch.put_item(Item=flight)

    print("SUCCESS: All flight data uploaded to DynamoDB table:", FLIGHTS_TABLE_NAME)

if __name__ == '__main__':
    main()
