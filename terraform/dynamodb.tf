# 1. Flights Table (Isse populate_flights_db.py bharega)
resource "aws_dynamodb_table" "flights_table" {
  provider       = aws.primary
  name           = "TravelEase-Flights"
  billing_mode   = "PAY_PER_REQUEST"
  hash_key       = "flight_id" 

  attribute {
    name = "flight_id"
    type = "S"
  }
  attribute {
    name = "route"
    type = "S"
  }
  global_secondary_index {
    name            = "route-index"
    hash_key        = "route"
    projection_type = "ALL"
  }
  tags = { Name = "${var.project_name}-flights-table" }
}

# 2. Bookings Table (Isse Booking Service istemaal karegi)
resource "aws_dynamodb_table" "bookings_db" {
  provider       = aws.primary
  name           = "BookingsDB"  # <-- Hum is naam ka istemaal karenge
  billing_mode   = "PAY_PER_REQUEST"
  hash_key       = "booking_reference"

  attribute {
    name = "booking_reference"
    type = "S"
  }
  tags = { Name = "${var.project_name}-bookings-table" }
}

# 3. Smart Trips Table (Isse Smart Trip feature istemaal karega)
resource "aws_dynamodb_table" "smart_trips_db" {
  provider     = aws.primary
  name         = "SmartTripsDB" # <-- Hum is naam ka istemaal karenge
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "trip_id"

  attribute {
    name = "trip_id"
    type = "S"
  }
}

# 4. IAM Policy (Sahi ki hui)
resource "aws_iam_policy" "dynamodb_access_policy" {
  name        = "${var.project_name}-DynamoDB-Access-Policy"
  description = "Allows ECS tasks to access TravelEase DynamoDB tables"

  policy = jsonencode({
    Version = "2012-10-17",
    Statement = [
      {
        Effect = "Allow",
        Action = [
          "dynamodb:Query",
          "dynamodb:Scan",
          "dynamodb:GetItem",
          "dynamodb:PutItem",
          "dynamodb:UpdateItem",
          "dynamodb:DeleteItem"
        ],
        Resource = [
          aws_dynamodb_table.flights_table.arn,
          aws_dynamodb_table.bookings_db.arn,     # <-- Sahi naam
          aws_dynamodb_table.smart_trips_db.arn,  # <-- Sahi naam
          "${aws_dynamodb_table.flights_table.arn}/index/route-index"
        ]
      }
    ]
  })
}
# 5. Seat Inventory Table (Isse Booking Service istemaal karegi)
resource "aws_dynamodb_table" "seat_inventory_table" {
  provider       = aws.primary
  name           = "SeatInventory"
  billing_mode   = "PAY_PER_REQUEST"
  hash_key       = "flight_id"    # e.g., "AI202_2025-12-01"
  range_key      = "seat_number"  # e.g., "3A"

  attribute {
    name = "flight_id"
    type = "S"
  }
  attribute {
    name = "seat_number"
    type = "S"
  }
  tags = { Name = "${var.project_name}-seat-inventory-table" }
}