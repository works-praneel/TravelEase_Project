resource "aws_ecr_repository" "booking_repo" {
  name = "booking-service"
}

resource "aws_ecr_repository" "flight_repo" {
  name = "flight-service"
}

resource "aws_ecr_repository" "payment_repo" {
  name = "payment-service"
}

# CrowdPulse ECR Repository
resource "aws_ecr_repository" "crowdpulse_repo" {
  name                 = "crowdpulse"
  image_tag_mutability = "MUTABLE"

  image_scanning_configuration {
    scan_on_push = true
  }

  tags = {
    Name = "CrowdPulse Repository"
  }
}
