resource "aws_ecr_repository" "booking_repo" {
  name = "booking-service"
}

resource "aws_ecr_repository" "flight_repo" {
  name = "flight-service"
}

resource "aws_ecr_repository" "payment_repo" {
  name = "payment-service"
}

resource "aws_ecr_repository" "crowdpulse_repo" {
  name = "crowdpulse-service"
}