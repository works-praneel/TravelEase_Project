import boto3
from decimal import Decimal

# --- Configuration ---
TABLE_NAME = "SmartTripsDB"  # Must match your dynamodb.tf file
REGION_NAME = "eu-north-1"   # Must match your provider.tf file
# ---------------------

#
# PART 1: HOTELS
# New hotel data as requested
#
hotel_data = [
    # --- Domestic Hotels ---
    {
        "trip_id": "HOTEL-001", "destination_code": "DEL", "name": "The Oberoi, New Delhi",
        "description": "5-star luxury hotel. Est. 1-day cab from DEL: ₹1500.", "price": 22000, "suggestion_type": "Hotel"
    },
    {
        "trip_id": "HOTEL-002", "destination_code": "BOM", "name": "The Taj Mahal Palace, Mumbai",
        "description": "5-star iconic hotel. Est. 1-day cab from BOM: ₹1200.", "price": 25000, "suggestion_type": "Hotel"
    },
    {
        "trip_id": "HOTEL-003", "destination_code": "CCU", "name": "ITC Royal Bengal, Kolkata",
        "description": "5-star luxury hotel. Est. 1-day cab from CCU: ₹800.", "price": 18000, "suggestion_type": "Hotel"
    },
    {
        "trip_id": "HOTEL-004", "destination_code": "MAA", "name": "The Leela Palace Chennai",
        "description": "5-star seaside hotel. Est. 1-day cab from MAA: ₹1000.", "price": 19000, "suggestion_type": "Hotel"
    },
    {
        "trip_id": "HOTEL-005", "destination_code": "GOI", "name": "Taj Exotica Resort & Spa, Goa",
        "description": "5-star beach resort. Est. 1-day cab from GOI: ₹2000.", "price": 24000, "suggestion_type": "Hotel"
    },
    {
        "trip_id": "HOTEL-006", "destination_code": "HYD", "name": "Taj Falaknuma Palace, Hyderabad",
        "description": "5-star palace hotel. Est. 1-day cab from HYD: ₹1800.", "price": 30000, "suggestion_type": "Hotel"
    },
    
    # --- International Hotels ---
    {
        "trip_id": "HOTEL-007", "destination_code": "HKT", "name": "Keemala, Phuket",
        "description": "5-star rainforest resort. Est. 1-day cab from HKT: ₹2500.", "price": 45000, "suggestion_type": "Hotel"
    },
    {
        "trip_id": "HOTEL-008", "destination_code": "SUB", "name": "Shangri-La Surabaya",
        "description": "5-star luxury hotel. Est. 1-day cab from SUB: ₹1000.", "price": 14000, "suggestion_type": "Hotel"
    },
    {
        "trip_id": "HOTEL-009", "destination_code": "NRT", "name": "The Peninsula Tokyo",
        "description": "5-star hotel near Ginza. Est. 1-day cab from NRT: ₹20000.", "price": 65000, "suggestion_type": "Hotel"
    },
    {
        "trip_id": "HOTEL-010", "destination_code": "HND", "name": "Park Hyatt Tokyo",
        "description": "5-star luxury hotel. Est. 1-day cab from HND: ₹8000.", "price": 70000, "suggestion_type": "Hotel"
    },
    {
        "trip_id": "HOTEL-011", "destination_code": "DXB", "name": "Burj Al Arab Jumeirah",
        "description": "7-star iconic hotel. Est. 1-day cab from DXB: ₹3000.", "price": 150000, "suggestion_type": "Hotel"
    },
    {
        "trip_id": "HOTEL-012", "destination_code": "SYD", "name": "Four Seasons Hotel Sydney",
        "description": "5-star hotel with Opera House views. Est. 1-day cab from SYD: ₹3500.", "price": 32000, "suggestion_type": "Hotel"
    },
    {
        "trip_id": "HOTEL-013", "destination_code": "MEL", "name": "The Langham, Melbourne",
        "description": "5-star hotel on the Yarra River. Est. 1-day cab from MEL: ₹4000.", "price": 28000, "suggestion_type": "Hotel"
    },
    {
        "trip_id": "HOTEL-014", "destination_code": "AKL", "name": "Cordis, Auckland",
        "description": "5-star luxury hotel. Est. 1-day cab from AKL: ₹4500.", "price": 26000, "suggestion_type": "Hotel"
    }
]


#
# PART 2: ACTIVITIES & TOURS
# This is the data from the previous step
#
activity_data = [
    # --- Domestic ---
    {
        "trip_id": "TRIP-001", "destination_code": "GOI", "name": "North Goa Beach Tour",
        "description": "A guided tour of Calangute and Baga beaches.", "price": 2500, "suggestion_type": "Activity"
    },
    {
        "trip_id": "TRIP-002", "destination_code": "GOI", "name": "South Goa Heritage Walk",
        "description": "Explore the history and architecture of Old Goa.", "price": 3000, "suggestion_type": "Tour"
    },
    {
        "trip_id": "TRIP-003", "destination_code": "DEL", "name": "Delhi Food Walk",
        "description": "Taste the best street food in Chandni Chowk.", "price": 2000, "suggestion_type": "Food"
    },
    {
        "trip_id": "TRIP-006", "destination_code": "DEL", "name": "Qutub Minar & Lotus Temple",
        "description": "Visit two of Delhi's most iconic landmarks.", "price": 3500, "suggestion_type": "Tour"
    },
    {
        "trip_id": "TRIP-007", "destination_code": "BOM", "name": "Elephanta Caves Tour",
        "description": "Ferry ride and tour of the ancient cave temples.", "price": 4000, "suggestion_type": "Tour"
    },
    {
        "trip_id": "TRIP-008", "destination_code": "BOM", "name": "Bollywood Film City Tour",
        "description": "Go behind the scenes of India's famous film industry.", "price": 5000, "suggestion_type": "Activity"
    },
    {
        "trip_id": "TRIP-009", "destination_code": "CCU", "name": "Victoria Memorial Hall",
        "description": "Explore the magnificent marble palace and museum.", "price": 1500, "suggestion_type": "Ticket"
    },
    {
        "trip_id": "TRIP-010", "destination_code": "CCU", "name": "Sundarbans Day Trip",
        "description": "A boat tour to the world's largest mangrove forest.", "price": 7000, "suggestion_type": "Tour"
    },
    {
        "trip_id": "TRIP-011", "destination_code": "MAA", "name": "Mahabalipuram Temples",
        "description": "Day trip to the ancient shore temples.", "price": 4500, "suggestion_type": "Tour"
    },
    {
        "trip_id": "TRIP-012", "destination_code": "MAA", "name": "Marina Beach Street Food",
        "description": "Enjoy local delicacies on India's longest urban beach.", "price": 1000, "suggestion_type": "Food"
    },
    {
        "trip_id": "TRIP-013", "destination_code": "HYD", "name": "Charminar & Laad Bazaar",
        "description": "Visit the iconic monument and shop for bangles.", "price": 1200, "suggestion_type": "Activity"
    },
    {
        "trip_id": "TRIP-014", "destination_code": "HYD", "name": "Ramoji Film City",
        "description": "Full day tour of the world's largest film studio complex.", "price": 6000, "suggestion_type": "Ticket"
    },
    
    # --- International ---
    {
        "trip_id": "TRIP-004", "destination_code": "DXB", "name": "Burj Khalifa At The Top",
        "description": "Visit the observation deck of the world's tallest building.", "price": 10500, "suggestion_type": "Ticket"
    },
    {
        "trip_id": "TRIP-005", "destination_code": "DXB", "name": "Desert Safari with BBQ",
        "description": "Dune bashing, camel rides, and BBQ dinner.", "price": 8000, "suggestion_type": "Activity"
    },
    {
        "trip_id": "TRIP-015", "destination_code": "HKT", "name": "Phi Phi Islands Tour",
        "description": "Speedboat tour to Maya Bay and Phi Phi Don.", "price": 7500, "suggestion_type": "Tour"
    },
    {
        "trip_id": "TRIP-016", "destination_code": "HKT", "name": "Phuket Big Buddha",
        "description": "Visit the iconic 45-meter tall marble statue.", "price": 2000, "suggestion_type": "Activity"
    },
    {
        "trip_id": "TRIP-017", "destination_code": "SUB", "name": "Mount Bromo Sunrise Tour",
        "description": "An unforgettable jeep tour to watch the sunrise over the volcano.", "price": 12000, "suggestion_type": "Tour"
    },
    {
        "trip_id": "TRIP-018", "destination_code": "SUB", "name": "Surabaya City Heritage",
        "description": "A tour of the 'City of Heroes' monuments and old town.", "price": 4000, "suggestion_type": "Tour"
    },
    {
        "trip_id": "TRIP-019", "destination_code": "NRT", "name": "Tokyo Disney Resort",
        "description": "1-Day Pass to either Disneyland or DisneySea.", "price": 15000, "suggestion_type": "Ticket"
    },
    {
        "trip_id": "TRIP-020", "destination_code": "NRT", "name": "Narita-san Shinsho-ji Temple",
        "description": "Explore the beautiful, large Buddhist temple complex near the airport.", "price": 1000, "suggestion_type": "Activity"
    },
    {
        "trip_id": "TRIP-021", "destination_code": "HND", "name": "Shibuya Crossing & Hachiko",
        "description": "Visit the world's busiest intersection and famous statue.", "price": 500, "suggestion_type": "Activity"
    },
    {
        "trip_id": "TRIP-022", "destination_code": "HND", "name": "teamLab Planets TOKYO",
        "description": "Immersive digital art museum experience.", "price": 6000, "suggestion_type": "Ticket"
    },
    {
        "trip_id": "TRIP-023", "destination_code": "SYD", "name": "Sydney Opera House Tour",
        "description": "A guided tour inside the iconic sail-like buildings.", "price": 5000, "suggestion_type": "Ticket"
    },
    {
        "trip_id": "TRIP-024", "destination_code": "SYD", "name": "Bondi Beach Surfing Lesson",
        "description": "Learn to surf at the world-famous Bondi Beach.", "price": 7000, "suggestion_type": "Activity"
    },
    {
        "trip_id": "TRIP-025", "destination_code": "MEL", "name": "Great Ocean Road Tour",
        "description": "Full-day trip to see the 12 Apostles rock formations.", "price": 11000, "suggestion_type": "Tour"
    },
    {
        "trip_id": "TRIP-026", "destination_code": "MEL", "name": "Phillip Island Penguin Parade",
        "description": "Watch hundreds of little penguins return to shore at sunset.", "price": 8500, "suggestion_type": "Ticket"
    },
    {
        "trip_id": "TRIP-027", "destination_code": "AKL", "name": "Hobbiton Movie Set Tour",
        "description": "A full-day tour from Auckland to the Lord of the Rings set.", "price": 18000, "suggestion_type": "Tour"
    },
    {
        "trip_id": "TRIP-028", "destination_code": "AKL", "name": "Auckland Sky Tower",
        "description": "Entry ticket to the observation deck of the tallest tower.", "price": 4000, "suggestion_type": "Ticket"
    }
]

# Combine both lists into one
all_smart_trips = hotel_data + activity_data


def populate_table():
    # Connect to DynamoDB
    try:
        dynamodb = boto3.resource('dynamodb', region_name=REGION_NAME)
        table = dynamodb.Table(TABLE_NAME)
        print(f"Successfully connected to table: {TABLE_NAME}")
    except Exception as e:
        print(f"Error connecting to DynamoDB: {e}")
        print("Please ensure your AWS credentials are set up and the table name is correct.")
        return

    # Use a batch_writer for efficient writing
    try:
        with table.batch_writer() as batch:
            # Iterate over the combined list
            for item in all_smart_trips:
                # Convert numbers to Decimal for DynamoDB
                item['price'] = Decimal(str(item['price']))
                
                print(f"Adding/Updating item: {item['trip_id']} - {item['name']}")
                batch.put_item(Item=item)
                
        print(f"\nSuccessfully populated/updated SmartTripsDB with {len(all_smart_trips)} items!")
        
    except Exception as e:
        print(f"Error during batch write: {e}")

if __name__ == "__main__":
    populate_table()